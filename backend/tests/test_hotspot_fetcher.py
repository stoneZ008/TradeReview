import pytest
import sys
import os
import time
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import hotspot_fetcher
from hotspot_fetcher import (
    get_hot_sectors,
    get_industry_sectors,
    get_sector_stocks,
    get_hot_stocks,
    get_fund_flow,
    get_stock_concepts,
    clear_cache,
    _safe_float,
    _parse_float,
    _parse_fund_flow,
    CACHE_DURATION
)

_format_number = _safe_float


class TestHotspotFetcherUtils:
    def test_format_number_with_none(self):
        assert _format_number(None) == 0

    def test_format_number_with_nan(self):
        import pandas as pd
        assert _format_number(pd.NA) == 0

    def test_format_number_with_string_percent(self):
        assert _format_number('5.6%') == 5.6

    def test_parse_float_with_dash(self):
        assert _parse_float('--') == 0

    def test_parse_fund_flow_with_yi(self):
        assert _parse_fund_flow('1.5亿') == 150000000

    def test_parse_fund_flow_with_wan(self):
        assert _parse_fund_flow('100万') == 1000000


class TestHotspotFetcherMock:
    @classmethod
    def setup_class(cls):
        clear_cache()

    def test_get_hot_sectors_mock_fallback(self):
        with patch('hotspot_fetcher._fetch_ths_concepts', side_effect=Exception('API Error')):
            sectors = get_hot_sectors(limit=10)
            assert len(sectors) > 0
            assert sectors[0]['is_mock'] == True
            assert 'name' in sectors[0]
            assert 'change_pct' in sectors[0]

    def test_get_industry_sectors_mock_fallback(self):
        with patch('hotspot_fetcher._fetch_ths_industries', side_effect=Exception('API Error')):
            sectors = get_industry_sectors(limit=10)
            assert len(sectors) > 0
            assert sectors[0]['is_mock'] == True

    def test_get_sector_stocks_mock_fallback(self):
        with patch('hotspot_fetcher._fetch_sector_stocks_em', side_effect=Exception('API Error')):
            stocks = get_sector_stocks('测试板块')
            assert len(stocks) > 0
            assert stocks[0]['is_mock'] == True

    def test_get_hot_stocks_mock_fallback(self):
        with patch('hotspot_fetcher._fetch_hot_stocks_cxg', side_effect=Exception('API Error')):
            stocks = get_hot_stocks(limit=10)
            assert len(stocks) > 0
            assert stocks[0]['is_mock'] == True

    def test_get_fund_flow_mock_fallback(self):
        with patch('hotspot_fetcher._fetch_fund_flow_ths', side_effect=Exception('API Error')):
            fund_flows = get_fund_flow()
            assert len(fund_flows) > 0
            assert fund_flows[0]['is_mock'] == True


class TestHotspotFetcherCache:
    @classmethod
    def setup_class(cls):
        clear_cache()

    def test_clear_cache(self):
        get_hot_sectors(limit=5)
        assert 'hot_sectors' in hotspot_fetcher._last_fetch_time
        clear_cache()
        assert 'hot_sectors' not in hotspot_fetcher._last_fetch_time

    def test_cache_validation(self):
        clear_cache()
        get_hot_sectors(limit=5)
        first_time = hotspot_fetcher._last_fetch_time.get('hot_sectors')
        assert first_time is not None
        
        get_hot_sectors(limit=5)
        second_time = hotspot_fetcher._last_fetch_time.get('hot_sectors')
        assert first_time == second_time

    def test_cache_expiration(self):
        clear_cache()
        get_hot_sectors(limit=5)
        first_time = hotspot_fetcher._last_fetch_time.get('hot_sectors')
        
        with patch('time.time', return_value=time.time() + CACHE_DURATION + 100):
            with patch('hotspot_fetcher._fetch_ths_concepts', side_effect=Exception('API Error')):
                get_hot_sectors.cache_clear()
                get_hot_sectors(limit=5)
        
        second_time = hotspot_fetcher._last_fetch_time.get('hot_sectors')
        assert second_time >= first_time + CACHE_DURATION


class TestStockConcepts:
    @classmethod
    def setup_class(cls):
        clear_cache()

    def test_get_stock_concepts_empty_cache(self):
        concepts = get_stock_concepts('000001')
        assert isinstance(concepts, list)

    def test_get_stock_concepts_invalid_code(self):
        concepts = get_stock_concepts('invalid')
        assert isinstance(concepts, list)
