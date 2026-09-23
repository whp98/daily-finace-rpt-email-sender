import yfinance as yf
from typing import Optional
from src.collectors.base import BaseCollector, format_volume
from src.models import AssetQuote

class YahooCollector(BaseCollector):
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def parse_quote(self, ticker: str, asset_def: dict) -> Optional[AssetQuote]:
        try:
            t = yf.Ticker(ticker)
            info = t.fast_info
            last = info.last_price
            prev = info.previous_close
            if last is None or prev is None:
                return None
            change_val = last - prev
            pct = (change_val / prev * 100.0) if prev != 0 else 0.0
            vol = getattr(info, 'last_volume', 0) or 0
            return AssetQuote(
                name=asset_def["name"],
                symbol=asset_def["symbol"],
                category=asset_def["category"],
                latest_price=f"{last:.2f}",
                prev_close=f"{prev:.2f}",
                change_pct=round(pct, 2),
                change_val=f"{change_val:+.2f}",
                volume=format_volume(vol),
                quote_time=""
            )
        except Exception:
            return None

    async def fetch_quotes(self, assets: list[dict]) -> dict[str, AssetQuote]:
        target_assets = [a for a in assets if a.get("yahoo_ticker")]
        results = {}
        for asset in target_assets:
            ticker = asset["yahoo_ticker"]
            q = self.parse_quote(ticker, asset)
            if q:
                results[asset["symbol"]] = q
        return results
