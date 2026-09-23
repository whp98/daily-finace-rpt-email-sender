import pytest
from src.models import AssetQuote
from src.config import load_assets_config, get_settings

def test_asset_quote_color_calc():
    q_up = AssetQuote(
        name="纳斯达克100", symbol="NDX100", category="欧美核心股指",
        latest_price="30732.40", prev_close="30482.35",
        change_pct=0.82, change_val="+250.05",
        volume="1.32B", quote_time="16:00:00"
    )
    assert q_up.color == "up"
    assert q_up.change_str == "+0.82%"

    q_down = AssetQuote(
        name="恒生指数", symbol="HSI", category="亚太重点股指",
        latest_price="24834.12", prev_close="25087.75",
        change_pct=-1.01, change_val="-253.63",
        volume="18.43M", quote_time="16:00:00"
    )
    assert q_down.color == "down"
    assert q_down.change_str == "-1.01%"

    q_flat = AssetQuote(
        name="平盘标的", symbol="FLAT", category="测试",
        latest_price="100.00", prev_close="100.00",
        change_pct=0.0, change_val="0.00",
        volume="-", quote_time="16:00:00"
    )
    assert q_flat.color == "flat"
    assert q_flat.change_str == "0.00%"

def test_load_assets_config():
    assets = load_assets_config("config/assets.yaml")
    assert len(assets) == 22
    categories = {a["category"] for a in assets}
    assert "欧美核心股指" in categories
    assert "亚太重点股指" in categories
    assert "大宗商品与贵金属" in categories
    assert "数字与恐慌资产" in categories
