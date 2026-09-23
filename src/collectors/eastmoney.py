import httpx
from typing import Optional
from src.collectors.base import BaseCollector, format_volume
from src.models import AssetQuote

class EastmoneyCollector(BaseCollector):
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "http://quote.eastmoney.com/"
        }

    def parse_quote(self, data: dict, asset_def: dict) -> Optional[AssetQuote]:
        try:
            raw_latest = data.get("f43")
            raw_prev = data.get("f60")
            if raw_latest is None or raw_prev is None or raw_latest == "-":
                return None
            latest = float(raw_latest) / 100.0
            prev = float(raw_prev) / 100.0
            change_pct = float(data.get("f170", 0)) / 100.0
            raw_val = data.get("f169", 0)
            change_val = f"{float(raw_val)/100.0:+.2f}" if raw_val != "-" else "0.00"
            vol = float(data.get("f47", 0)) if data.get("f47") != "-" else 0

            return AssetQuote(
                name=asset_def["name"],
                symbol=asset_def["symbol"],
                category=asset_def["category"],
                latest_price=f"{latest:.2f}",
                prev_close=f"{prev:.2f}",
                change_pct=change_pct,
                change_val=change_val,
                volume=format_volume(vol),
                quote_time=str(data.get("f124", ""))
            )
        except Exception:
            return None

    async def fetch_quotes(self, assets: list[dict]) -> dict[str, AssetQuote]:
        target_assets = [a for a in assets if a.get("eastmoney_secid")]
        results = {}
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            for asset in target_assets:
                secid = asset["eastmoney_secid"]
                url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f57,f58,f43,f60,f169,f170,f47,f124"
                try:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        payload = resp.json().get("data")
                        if payload:
                            q = self.parse_quote(payload, asset)
                            if q:
                                results[asset["symbol"]] = q
                except Exception:
                    pass
        return results
