import httpx
from typing import Optional
from src.collectors.base import BaseCollector, format_volume
from src.models import AssetQuote

class TencentCollector(BaseCollector):
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.headers = {"User-Agent": "Mozilla/5.0"}

    def parse_line(self, line: str, asset_def: dict) -> Optional[AssetQuote]:
        # v_s_usVIX="200~标普500波动率指数~.VIX~21.67~-0.12~-0.55~0~0~~";
        # v_s_sh000001="1~上证指数~000001~3936.52~-15.61~-0.39~466913933~83413286~~"
        try:
            if '="' not in line:
                return None
            _, content = line.split('="', 1)
            raw = content.rstrip('";').strip()
            parts = raw.split("~")
            if len(parts) < 7:
                return None
            latest = float(parts[3])
            change_val = float(parts[4])
            change_pct = float(parts[5])
            prev = latest - change_val
            vol = float(parts[6]) if parts[6] else 0
            return AssetQuote(
                name=asset_def["name"],
                symbol=asset_def["symbol"],
                category=asset_def["category"],
                latest_price=f"{latest:.2f}",
                prev_close=f"{prev:.2f}",
                change_pct=change_pct,
                change_val=f"{change_val:+.2f}",
                volume=format_volume(vol)
            )
        except Exception:
            return None

    async def fetch_quotes(self, assets: list[dict]) -> dict[str, AssetQuote]:
        target_assets = [a for a in assets if a.get("tencent_code")]
        if not target_assets:
            return {}
        codes = [a["tencent_code"] for a in target_assets]
        url = "https://qt.gtimg.cn/q=" + ",".join(codes)
        results = {}
        code_to_asset = {a["tencent_code"]: a for a in target_assets}
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    text = resp.content.decode("gbk", errors="ignore")
                    for line in text.strip().split(";"):
                        line = line.strip()
                        if not line or '="' not in line:
                            continue
                        prefix = line.split('="')[0].replace("v_", "").strip()
                        asset_def = code_to_asset.get(prefix)
                        if asset_def:
                            q = self.parse_line(line, asset_def)
                            if q:
                                results[asset_def["symbol"]] = q
            except Exception:
                pass
        return results
