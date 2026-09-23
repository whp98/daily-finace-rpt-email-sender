import asyncio
from typing import Optional
from src.models import AssetQuote
from src.collectors.eastmoney import EastmoneyCollector
from src.collectors.sina import SinaCollector
from src.collectors.tencent import TencentCollector

class QuoteAggregator:
    def __init__(self, timeout: float = 6.0):
        self.eastmoney = EastmoneyCollector(timeout=timeout)
        self.sina = SinaCollector(timeout=timeout)
        self.tencent = TencentCollector(timeout=timeout)

    async def collect_all(self, assets: list[dict]) -> list[AssetQuote]:
        # 并发向三大源发起请求
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
        for asset in assets:
            sym = asset["symbol"]
            # 优先级合并：新浪(期货/现货/外汇佳) > 腾讯(国内/VIX) > 东财(全球股指)
            q = dict_sina.get(sym) or dict_tenc.get(sym) or dict_east.get(sym)
            if not q:
                # 兜底生成缺省休市对象
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
