from abc import ABC, abstractmethod
from typing import Optional
from src.models import AssetQuote

def format_volume(vol: float) -> str:
    if vol <= 0:
        return "-"
    if vol >= 1e9:
        return f"{vol/1e9:.2f}B"
    if vol >= 1e6:
        return f"{vol/1e6:.2f}M"
    if vol >= 1e3:
        return f"{vol/1e3:.2f}K"
    return f"{vol:.0f}"

class BaseCollector(ABC):
    @abstractmethod
    async def fetch_quotes(self, assets: list[dict]) -> dict[str, AssetQuote]:
        """批量获取行情字典：{symbol: AssetQuote}"""
        pass
