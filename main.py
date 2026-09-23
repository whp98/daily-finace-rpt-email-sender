import argparse
import asyncio
from datetime import datetime
import zoneinfo
from src.config import get_settings, load_assets_config
from src.collectors.aggregator import QuoteAggregator
from src.renderer import ReportRenderer
from src.mailer import GmailMailer

async def run(report_type: str = "morning", dry_run: bool = False, output_file: str = "test_report.html"):
    settings = get_settings()
    tz = zoneinfo.ZoneInfo(settings.timezone)
    now_dt = datetime.now(tz)
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    date_str = now_dt.strftime("%Y-%m-%d")

    print(f"[{now_str}] 正在启动全球宏观财经简报采集 (类型: {report_type})...")
    assets = load_assets_config()
    aggregator = QuoteAggregator()
    quotes = await aggregator.collect_all(assets)

    print(f"[{now_str}] 成功获取 {len(quotes)} 个标的数据:")
    print("=" * 72)
    print(f"{'标的名称':<18} {'最新价':<12} {'昨收盘':<12} {'涨跌幅':<10} {'成交量':<8}")
    print("-" * 72)
    for q in quotes:
        print(f"{q.name:<18} {q.latest_price:<12} {q.prev_close:<12} {q.change_str:<10} {q.volume:<8}")
    print("=" * 72)

    renderer = ReportRenderer()
    html = renderer.render(quotes, report_type=report_type, date_str=date_str)

    # 如果指定 dry_run，或者未配置 Gmail 账户，则仅生成本地 HTML 预览文件
    if dry_run or not settings.gmail_user or not settings.gmail_app_password:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[{now_str}] [本地调试模式] 邮件 HTML 预览已生成: {output_file}")
        return True

    subject = f"【全球财经{'晨报' if report_type == 'morning' else '晚报'}】{date_str}"
    mailer = GmailMailer(settings)
    ok = mailer.send(subject=subject, html_content=html)
    if ok:
        print(f"[{now_str}] 邮件成功发送至: {settings.email_to}")
    else:
        print(f"[{now_str}] 邮件发送失败，已同时写入本地备份: {output_file}")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)
    return ok

def main():
    parser = argparse.ArgumentParser(description="全球宏观财经每日邮件简报系统")
    parser.add_argument("--report-type", choices=["morning", "evening", "auto"], default="auto")
    parser.add_argument("--dry-run", action="store_true", help="本地抓取与预览模式，不发送真实邮件")
    parser.add_argument("--output", default="test_report.html", help="HTML 预览输出文件名")
    args = parser.parse_args()

    rtype = args.report_type
    if rtype == "auto":
        settings = get_settings()
        tz = zoneinfo.ZoneInfo(settings.timezone)
        now_hour = datetime.now(tz).hour
        rtype = "evening" if 13 <= now_hour <= 22 else "morning"

    asyncio.run(run(report_type=rtype, dry_run=args.dry_run, output_file=args.output))

if __name__ == "__main__":
    main()
