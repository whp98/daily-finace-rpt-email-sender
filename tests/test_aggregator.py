import pytest
from unittest.mock import AsyncMock, patch
from src.collectors.aggregator import QuoteAggregator
from src.models import AssetQuote

@pytest.mark.asyncio
async def test_aggregator_merging():
    assets = [
        {"name": "标普500", "symbol": "SPX", "category": "欧美核心股指"},
        {"name": "WTI原油", "symbol": "CL", "category": "大宗商品与贵金属"}
    ]
    aggregator = QuoteAggregator()

    # 模拟东财采集到 SPX，新浪采集到 CL
    mock_east = {"SPX": AssetQuote(
        name="标普500", symbol="SPX", category="欧美核心股指",
        latest_price="7764.64", prev_close="7764.70", change_pct=0.0, change_val="0.00"
    )}
    mock_sina = {"CL": AssetQuote(
        name="WTI原油", symbol="CL", category="大宗商品与贵金属",
        latest_price="90.25", prev_close="89.89", change_pct=0.4, change_val="+0.36"
    )}

    with patch.object(aggregator.eastmoney, "fetch_quotes", new_callable=AsyncMock) as m_east, \
         patch.object(aggregator.sina, "fetch_quotes", new_callable=AsyncMock) as m_sina, \
         patch.object(aggregator.tencent, "fetch_quotes", new_callable=AsyncMock) as m_tenc:
        m_east.return_value = mock_east
        m_sina.return_value = mock_sina
        m_tenc.return_value = {}

        quotes = await aggregator.collect_all(assets)
        assert len(quotes) == 2
        assert quotes[0].symbol == "SPX"
        assert quotes[0].latest_price == "7764.64"
        assert quotes[1].symbol == "CL"
        assert quotes[1].latest_price == "90.25"

@pytest.mark.asyncio
async def test_aggregator_fallback_empty():
    assets = [
        {"name": "未知品种", "symbol": "UNKNOWN", "category": "测试"}
    ]
    aggregator = QuoteAggregator()
    with patch.object(aggregator.eastmoney, "fetch_quotes", new_callable=AsyncMock) as m_east, \
         patch.object(aggregator.sina, "fetch_quotes", new_callable=AsyncMock) as m_sina, \
         patch.object(aggregator.tencent, "fetch_quotes", new_callable=AsyncMock) as m_tenc:
        m_east.return_value = {}
        m_sina.return_value = {}
        m_tenc.return_value = {}

        quotes = await aggregator.collect_all(assets)
        assert len(quotes) == 1
        assert quotes[0].symbol == "UNKNOWN"
        assert quotes[0].latest_price == "-"
        assert quotes[0].status == "nodata"
