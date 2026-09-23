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

@pytest.mark.asyncio
async def test_aggregator_switches_when_source_invalid():
    # 测试：当优先级更高的新浪数据源返回缺失点位/涨跌（如 '-'）时，自动切换至下一个有效数据源（腾讯）
    assets = [
        {"name": "纳斯达克100", "symbol": "NDX100", "category": "欧美核心股指"}
    ]
    aggregator = QuoteAggregator()
    bad_sina = {"NDX100": AssetQuote(
        name="纳斯达克100", symbol="NDX100", category="欧美核心股指",
        latest_price="-", prev_close="-", change_pct=0.0, change_val="-", status="nodata"
    )}
    good_tenc = {"NDX100": AssetQuote(
        name="纳斯达克100", symbol="NDX100", category="欧美核心股指",
        latest_price="30732.40", prev_close="30482.35", change_pct=0.82, change_val="+250.05"
    )}

    with patch.object(aggregator.sina, "fetch_quotes", new_callable=AsyncMock) as m_sina, \
         patch.object(aggregator.tencent, "fetch_quotes", new_callable=AsyncMock) as m_tenc, \
         patch.object(aggregator.eastmoney, "fetch_quotes", new_callable=AsyncMock) as m_east:
        m_sina.return_value = bad_sina
        m_tenc.return_value = good_tenc
        m_east.return_value = {}

        quotes = await aggregator.collect_all(assets)
        assert len(quotes) == 1
        assert quotes[0].latest_price == "30732.40"
        assert quotes[0].change_pct == 0.82
        assert quotes[0].change_val == "+250.05"

@pytest.mark.asyncio
async def test_aggregator_prefers_source_with_movement():
    # 测试：当第一数据源涨跌为 0（无变动/未更新），而第二数据源有真实涨跌时，优先切换至有实际变动的数据源
    assets = [
        {"name": "纳斯达克100", "symbol": "NDX100", "category": "欧美核心股指"}
    ]
    aggregator = QuoteAggregator()
    flat_sina = {"NDX100": AssetQuote(
        name="纳斯达克100", symbol="NDX100", category="欧美核心股指",
        latest_price="30482.35", prev_close="30482.35", change_pct=0.0, change_val="0.00"
    )}
    active_tenc = {"NDX100": AssetQuote(
        name="纳斯达克100", symbol="NDX100", category="欧美核心股指",
        latest_price="30732.40", prev_close="30482.35", change_pct=0.82, change_val="+250.05"
    )}

    with patch.object(aggregator.sina, "fetch_quotes", new_callable=AsyncMock) as m_sina, \
         patch.object(aggregator.tencent, "fetch_quotes", new_callable=AsyncMock) as m_tenc, \
         patch.object(aggregator.eastmoney, "fetch_quotes", new_callable=AsyncMock) as m_east:
        m_sina.return_value = flat_sina
        m_tenc.return_value = active_tenc
        m_east.return_value = {}

        quotes = await aggregator.collect_all(assets)
        assert len(quotes) == 1
        assert quotes[0].latest_price == "30732.40"
        assert quotes[0].change_pct == 0.82
