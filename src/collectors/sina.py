import httpx
from typing import Optional
from src.collectors.base import BaseCollector, format_volume
from src.models import AssetQuote

class SinaCollector(BaseCollector):
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://finance.sina.com.cn"
        }

    def parse_hf_quote(self, code: str, raw_str: str, asset_def: dict) -> Optional[AssetQuote]:
        # hf_CL="90.250,,90.200,90.220,90.520,88.710,16:42:52,90.520,89.890..."
        parts = raw_str.split(",")
        if len(parts) < 14:
            return None
        try:
            latest = float(parts[0])
            prev = float(parts[8]) if parts[8] else latest
            change_val = latest - prev
            pct = (change_val / prev * 100.0) if prev != 0 else 0.0
            time_str = parts[6] if len(parts) > 6 else ""
            return AssetQuote(
                name=asset_def["name"],
                symbol=asset_def["symbol"],
                category=asset_def["category"],
                latest_price=f"{latest:.2f}",
                prev_close=f"{prev:.2f}",
                change_pct=round(pct, 2),
                change_val=f"{change_val:+.2f}",
                volume="-",
                quote_time=time_str
            )
        except Exception:
            return None

    def parse_fx_quote(self, code: str, raw_str: str, asset_def: dict) -> Optional[AssetQuote]:
        # fx_sxauusd="16:43:02,4316.73,4316.73,4357.47,589628,4357.47,4372.8..."
        parts = raw_str.split(",")
        if len(parts) < 4:
            return None
        try:
            time_str = parts[0]
            latest = float(parts[1])
            prev = float(parts[3]) if parts[3] else latest
            change_val = latest - prev
            pct = (change_val / prev * 100.0) if prev != 0 else 0.0
            return AssetQuote(
                name=asset_def["name"],
                symbol=asset_def["symbol"],
                category=asset_def["category"],
                latest_price=f"{latest:.2f}",
                prev_close=f"{prev:.2f}",
                change_pct=round(pct, 2),
                change_val=f"{change_val:+.2f}",
                volume="-",
                quote_time=time_str
            )
        except Exception:
            return None

    def parse_int_quote(self, code: str, raw_str: str, asset_def: dict) -> Optional[AssetQuote]:
        # int_ftse="伦敦指数,9284.83,70.85,0.77"
        # Format: name, latest, change_val, change_pct
        parts = raw_str.split(",")
        if len(parts) < 4:
            return None
        try:
            latest = float(parts[1])
            change_val = float(parts[2])
            change_pct = float(parts[3])
            prev = latest - change_val
            return AssetQuote(
                name=asset_def["name"],
                symbol=asset_def["symbol"],
                category=asset_def["category"],
                latest_price=f"{latest:.2f}",
                prev_close=f"{prev:.2f}",
                change_pct=change_pct,
                change_val=f"{change_val:+.2f}",
                volume="-",
                quote_time=""
            )
        except Exception:
            return None

    def parse_b_quote(self, code: str, raw_str: str, asset_def: dict) -> Optional[AssetQuote]:
        # b_TWSE="台湾台北指数,25580.32,-443.53,-1.70,9/26/2025,..."
        # b_KOSPI="韩国KOSPI指数,7080.9200,63.01,0.90,..."
        # Format: name, latest, change_val, change_pct, ...
        parts = raw_str.split(",")
        if len(parts) < 4:
            return None
        try:
            latest = float(parts[1])
            change_val = float(parts[2])
            change_pct = float(parts[3])
            prev = latest - change_val
            return AssetQuote(
                name=asset_def["name"],
                symbol=asset_def["symbol"],
                category=asset_def["category"],
                latest_price=f"{latest:.2f}",
                prev_close=f"{prev:.2f}",
                change_pct=change_pct,
                change_val=f"{change_val:+.2f}",
                volume="-",
                quote_time=""
            )
        except Exception:
            return None

    def parse_gb_quote(self, code: str, raw_str: str, asset_def: dict) -> Optional[AssetQuote]:
        # Format: name, latest, change_pct(%), datetime, change_val, open, high, low, ..., volume(parts[10]), ..., prev_close(parts[26])
        parts = raw_str.split(",")
        if len(parts) < 5:
            return None
        try:
            latest = float(parts[1])
            change_pct = float(parts[2])
            time_str = parts[3] if len(parts) > 3 else ""
            change_val = float(parts[4]) if len(parts) > 4 else 0.0
            if len(parts) > 26 and parts[26]:
                prev = float(parts[26])
            else:
                prev = latest - change_val
            vol_str = parts[10] if len(parts) > 10 and parts[10] else ""
            vol = float(vol_str) if vol_str else 0.0
            return AssetQuote(
                name=asset_def["name"],
                symbol=asset_def["symbol"],
                category=asset_def["category"],
                latest_price=f"{latest:.2f}",
                prev_close=f"{prev:.2f}",
                change_pct=change_pct,
                change_val=f"{change_val:+.2f}",
                volume=format_volume(vol),
                quote_time=time_str
            )
        except Exception:
            return None

    async def fetch_quotes(self, assets: list[dict]) -> dict[str, AssetQuote]:
        target_assets = [a for a in assets if a.get("sina_code")]
        if not target_assets:
            return {}
        codes = [a["sina_code"] for a in target_assets]
        url = "https://hq.sinajs.cn/list=" + ",".join(codes)
        results = {}
        code_to_asset = {a["sina_code"]: a for a in target_assets}
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    text = resp.content.decode("gbk", errors="ignore")
                    for line in text.strip().split("\n"):
                        if '="' not in line:
                            continue
                        code_part, data_part = line.split('="', 1)
                        clean_code = code_part.replace("var hq_str_", "").strip()
                        raw_data = data_part.rstrip('";')
                        if not raw_data:
                            continue
                        asset_def = code_to_asset.get(clean_code)
                        if not asset_def:
                            continue
                        if clean_code.startswith("hf_"):
                            q = self.parse_hf_quote(clean_code, raw_data, asset_def)
                        elif clean_code.startswith("fx_"):
                            q = self.parse_fx_quote(clean_code, raw_data, asset_def)
                        elif clean_code.startswith("int_"):
                            q = self.parse_int_quote(clean_code, raw_data, asset_def)
                        elif clean_code.startswith("b_"):
                            q = self.parse_b_quote(clean_code, raw_data, asset_def)
                        elif clean_code.startswith("gb_"):
                            q = self.parse_gb_quote(clean_code, raw_data, asset_def)
                        else:
                            q = None
                        if q:
                            results[asset_def["symbol"]] = q
            except Exception:
                pass
        return results
