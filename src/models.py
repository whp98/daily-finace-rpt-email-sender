from pydantic import BaseModel
from typing import Optional

class AssetQuote(BaseModel):
    name: str
    symbol: str
    category: str
    latest_price: str
    prev_close: str
    change_pct: float
    change_val: str
    volume: str = "-"
    quote_time: str = ""
    status: str = "normal"

    @property
    def color(self) -> str:
        if self.change_pct > 0.0001:
            return "up"
        elif self.change_pct < -0.0001:
            return "down"
        return "flat"

    @property
    def change_str(self) -> str:
        if self.change_pct > 0.0001:
            return f"+{self.change_pct:.2f}%"
        elif self.change_pct < -0.0001:
            return f"{self.change_pct:.2f}%"
        return "0.00%"
