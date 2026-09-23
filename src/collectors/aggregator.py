import asyncio
from typing import Optional
from src.models import AssetQuote
from src.collectors.eastmoney import EastmoneyCollector
from src.collectors.sina import SinaCollector
from src.collectors.tencent import TencentCollector
from src.collectors.yahoo import YahooCollector

def is_valid_quote(q: Optional[AssetQuote]) -> bool:
    """
    检查数据源返回的行情是否有效：
    1. 必须非空且 status != 'nodata'
    2. 点位必须有效（latest_price 和 prev_close 非空且数值大于 0）
    3. 涨跌必须有效（change_val 必须存在且不为 '-'）
    """
    if not q or q.status == "nodata":
        return False

    if not q.latest_price or q.latest_price in ("-", "0", "0.0", "0.00"):
        return False
    try:
        latest = float(q.latest_price)
        if latest <= 0:
            return False
    except (ValueError, TypeError):
        return False

    if not q.prev_close or q.prev_close in ("-", "0", "0.0", "0.00"):
        return False
    try:
        prev = float(q.prev_close)
        if prev <= 0:
            return False
    except (ValueError, TypeError):
        return False

    if not q.change_val or q.change_val == "-":
        return False

    return True

def has_movement(q: AssetQuote) -> bool:
    """判断行情是否有明确涨跌变动（非 0 变动）"""
    try:
        if abs(q.change_pct) > 0.0001:
            return True
        if float(q.change_val) != 0.0:
            return True
    except (ValueError, TypeError):
        pass
    return False

class QuoteAggregator:
    def __init__(self, timeout: float = 6.0):
        self.eastmoney = EastmoneyCollector(timeout=timeout)
        self.sina = SinaCollector(timeout=timeout)
        self.tencent = TencentCollector(timeout=timeout)
        self.yahoo = YahooCollector(timeout=timeout)

    async def collect_all(self, assets: list[dict]) -> list[AssetQuote]:
        t_east = asyncio.create_task(self.eastmoney.fetch_quotes(assets))
        t_sina = asyncio.create_task(self.sina.fetch_quotes(assets))
        t_tenc = asyncio.create_task(self.tencent.fetch_quotes(assets))

        res_east, res_sina, res_tenc = await asyncio.gather(
            t_east, t_sina, t_tenc, return_exceptions=True
        )

        dict_east = res_east if isinstance(res_east, dict) else {}
        dict_sina = res_sina if isinstance(res_sina, dict) else {}
        dict_tenc = res_tenc if isinstance(res_tenc, dict) else {}

        quotes: list[AssetQuote] = []
        missing_assets = []
        for asset in assets:
            sym = asset["symbol"]
            candidates = [
                dict_sina.get(sym),
                dict_tenc.get(sym),
                dict_east.get(sym),
            ]
            valid_candidates = [c for c in candidates if is_valid_quote(c)]

            # 优先选择有实际涨跌变动的有效数据源
            selected: Optional[AssetQuote] = None
            for c in valid_candidates:
                if has_movement(c):
                    selected = c
                    break

            # 若所有有效源涨跌均为 0（例如当天收平或停牌），则按优先级取第一个有效源
            if not selected and valid_candidates:
                selected = valid_candidates[0]

            if selected:
                quotes.append(selected)
            else:
                missing_assets.append(asset)

        if missing_assets:
            try:
                dict_yahoo = await self.yahoo.fetch_quotes(missing_assets)
            except Exception:
                dict_yahoo = {}
            for asset in missing_assets:
                sym = asset["symbol"]
                q = dict_yahoo.get(sym)
                if not is_valid_quote(q):
                    q = AssetQuote(
                        name=asset["name"],
                        symbol=sym,
                        category=asset["category"],
                        latest_price="-",
                        prev_close="-",
                        change_pct=0.0,
                        change_val="-",
                        volume="-",
                        quote_time="",
                        status="nodata"
                    )
                quotes.append(q)

        return quotes
