import pytest
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from attribution_analyzer import (
    analyze_stock_attribution,
    analyze_sector_attribution,
    get_market_overview,
    _detect_technical_signals,
    _calculate_driving_factors
)


class TestTechnicalSignals:
    def test_detect_strong_rise(self):
        signals = _detect_technical_signals(6, 50000000, 10)
        assert '放量大涨' in signals

    def test_detect_normal_rise(self):
        signals = _detect_technical_signals(4, 10000000, 10)
        assert '强势上涨' in signals

    def test_detect_strong_fall(self):
        signals = _detect_technical_signals(-6, -50000000, 10)
        assert '放量大跌' in signals

    def test_detect_major_inflow(self):
        signals = _detect_technical_signals(1, 150000000, 10)
        assert '主力大幅流入' in signals

    def test_detect_consolidation(self):
        signals = _detect_technical_signals(0.5, 1000000, 10)
        assert '震荡整理' in signals

    def test_signal_limit(self):
        signals = _detect_technical_signals(10, 200000000, 10)
        assert len(signals) <= 4


class TestStockAttribution:
    def test_analyze_stock_attribution_structure(self):
        result = analyze_stock_attribution('000001', '测试股票')
        assert result['code'] == '000001'
        assert result['name'] == '测试股票'
        assert 'change_pct' in result
        assert 'price' in result
        assert 'attribution' in result
        assert 'fund_flow' in result
        assert 'technical_signals' in result

    def test_analyze_stock_attribution_concepts(self):
        with patch('attribution_analyzer.get_stock_concepts', return_value=['AI', '芯片']):
            result = analyze_stock_attribution('000001')
            assert len(result['attribution']['concepts']) == 2

    def test_analyze_stock_attribution_no_concepts(self):
        with patch('attribution_analyzer.get_stock_concepts', return_value=[]):
            result = analyze_stock_attribution('000001')
            assert result['attribution']['concepts'] == []


class TestSectorAttribution:
    def test_analyze_sector_attribution_structure(self):
        result = analyze_sector_attribution('AI')
        assert result['sector_name'] == 'AI'
        assert 'change_pct' in result
        assert 'stock_count' in result
        assert 'lead_stocks' in result
        assert 'driving_factors' in result
        assert 'weak_stocks' in result

    def test_analyze_sector_attribution_lead_stocks(self):
        result = analyze_sector_attribution('AI')
        changes = [s['change_pct'] for s in result['lead_stocks']]
        assert changes == sorted(changes, reverse=True)

    def test_analyze_sector_attribution_driving_factors_sum(self):
        result = analyze_sector_attribution('AI')
        total_weight = sum(f['weight'] for f in result['driving_factors'])
        assert abs(total_weight - 1.0) < 0.01

    def test_calculate_driving_factors_positive(self):
        stocks = [{'change_pct': 5, 'fund_net_inflow': 100000000}]
        factors = _calculate_driving_factors(stocks, 5)
        assert any(f['type'] == '资金推动' for f in factors)

    def test_calculate_driving_factors_negative(self):
        stocks = [{'change_pct': -5, 'fund_net_inflow': -100000000}]
        factors = _calculate_driving_factors(stocks, -5)
        assert any(f['type'] == '情绪回落' for f in factors)


class TestMarketOverview:
    def test_get_market_overview_structure(self):
        result = get_market_overview()
        assert 'market_status' in result
        assert 'hot_topic' in result

    def test_get_market_overview_valid_status(self):
        result = get_market_overview()
        assert result['market_status'] in ['强势', '震荡', '弱势']
