import pytest
from src.renderer import ReportRenderer
from src.models import AssetQuote

def test_renderer_html_generation():
    renderer = ReportRenderer()
    sample_quotes = [
        AssetQuote(
            name="纳斯达克100", symbol="NDX100", category="欧美核心股指",
            latest_price="30732.40", prev_close="30482.35",
            change_pct=0.82, change_val="+250.05",
            volume="1.32B", quote_time="16:00:00"
        ),
        AssetQuote(
            name="香港恒生指数", symbol="HSI", category="亚太重点股指",
            latest_price="24834.12", prev_close="25087.75",
            change_pct=-1.01, change_val="-253.63",
            volume="18.43M", quote_time="16:00:00"
        )
    ]
    html = renderer.render(quotes=sample_quotes, report_type="morning", date_str="2026-09-23")
    assert "全球财经晨报" in html
    assert "30732.40" in html
    assert "+0.82%" in html
    assert "#e53935" in html  # 红涨颜色
    assert "#2e7d32" in html  # 绿跌颜色
    assert "欧美核心股指" in html
    assert "亚太重点股指" in html
