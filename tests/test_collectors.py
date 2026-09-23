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
