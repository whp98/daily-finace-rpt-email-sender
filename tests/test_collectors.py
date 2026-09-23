import pytest
from unittest.mock import patch, MagicMock
from src.collectors.eastmoney import EastmoneyCollector
from src.collectors.sina import SinaCollector
from src.collectors.tencent import TencentCollector

def test_parse_eastmoney_stock():
    collector = EastmoneyCollector()
    mock_data = {
        "f57": "SPX", "f58": "标普500",
        "f43": 776464, "f60": 776470,
        "f169": -6, "f170": 0, "f47": 3164537854
    }
    quote = collector.parse_quote(mock_data, {"name": "标普500指数", "symbol": "SPX", "category": "欧美核心股指"})
    assert quote is not None
    assert quote.latest_price == "7764.64"
    assert quote.prev_close == "7764.70"
    assert quote.change_pct == 0.0

def test_parse_sina_futures():
    collector = SinaCollector()
    raw_str = '90.250,,90.200,90.220,90.520,88.710,16:42:52,90.520,89.890,0,10,4,2026-09-23,纽约原油,0'
    quote = collector.parse_hf_quote("hf_CL", raw_str, {"name": "WTI原油", "symbol": "CL", "category": "大宗商品与贵金属"})
    assert quote is not None
    assert quote.latest_price == "90.25"
    assert quote.prev_close == "89.89"
    assert quote.color == "up"

def test_parse_tencent_quote():
    collector = TencentCollector()
    raw_line = 'v_s_usVIX="200~标普500波动率指数~.VIX~21.67~-0.12~-0.55~0~0~~";'
    quote = collector.parse_line(raw_line, {"name": "VIX恐慌指数", "symbol": "VIX", "category": "数字与恐慌资产"})
    assert quote is not None
    assert quote.latest_price == "21.67"
    assert quote.change_pct == -0.55
    assert quote.color == "down"

def test_parse_sina_international_index():
    collector = SinaCollector()
    raw_str = '伦敦指数,9284.83,70.85,0.77'
    quote = collector.parse_int_quote("int_ftse", raw_str, {"name": "英国富时100", "symbol": "FTSE", "category": "欧美核心股指"})
    assert quote is not None
    assert quote.latest_price == "9284.83"
    assert quote.change_pct == 0.77
    assert quote.color == "up"

def test_parse_sina_b_index():
    collector = SinaCollector()
    raw_str = '台湾台北指数,25580.32,-443.53,-1.70,9/26/2025,2025-09-26'
    quote = collector.parse_b_quote("b_TWSE", raw_str, {"name": "台湾加权指数", "symbol": "TWII", "category": "亚太重点股指"})
    assert quote is not None
    assert quote.latest_price == "25580.32"
    assert quote.change_pct == -1.70
    assert quote.color == "down"

def test_parse_sina_gb_quote():
    collector = SinaCollector()
    raw_str = '纳斯达克100,30732.3956,0.82,2026-09-23 09:48:45,250.0431,30496.4323,30770.6291,30496.4323,30762.1992,22841.4180,1329914531,1264453510,0,0.00,--,0.00,0.00,0.00,0.00,0,0,0.0000,0.00,0.00,,Sep 22 05:15PM EDT,30482.3525'
    quote = collector.parse_gb_quote("gb_ndx", raw_str, {"name": "纳斯达克100", "symbol": "NDX100", "category": "欧美核心股指"})
    assert quote is not None
    assert quote.latest_price == "30732.40"
    assert quote.prev_close == "30482.35"
    assert quote.change_pct == 0.82
    assert quote.change_val == "+250.04"
    assert quote.volume == "1.33B"
    assert quote.color == "up"

@patch("src.collectors.yahoo.yf.Ticker")
def test_yahoo_collector_mocked(mock_ticker):
    from src.collectors.yahoo import YahooCollector
    mock_instance = MagicMock()
    mock_instance.fast_info.last_price = 8150.0
    mock_instance.fast_info.previous_close = 8100.0
    mock_instance.fast_info.last_volume = 1000000
    mock_ticker.return_value = mock_instance

    collector = YahooCollector()
    asset = {"name": "法国CAC40", "symbol": "FCHI", "category": "欧美核心股指", "yahoo_ticker": "^FCHI"}
    result = collector.parse_quote("^FCHI", asset)
    assert result is not None
    assert result.latest_price == "8150.00"
    assert result.prev_close == "8100.00"
    assert result.change_pct == 0.62
    assert result.color == "up"
