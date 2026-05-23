import pandas as pd
import numpy as np
from indicators import calculate_sma, calculate_boll, calculate_macd, calculate_rsi, calculate_kdj


def test_calculate_sma():
    """测试均线计算"""
    data = pd.DataFrame({
        'close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
    })
    result = calculate_sma(data['close'], period=5)
    assert not pd.isna(result.iloc[4])


def test_calculate_boll():
    """测试布林带计算"""
    data = pd.DataFrame({
        'close': np.random.rand(50) * 100 + 100
    })
    result = calculate_boll(data)
    assert 'upper' in result.columns
    assert 'middle' in result.columns
    assert 'lower' in result.columns


def test_calculate_macd():
    """测试MACD计算"""
    data = pd.DataFrame({
        'close': np.random.rand(50) * 100 + 100
    })
    result = calculate_macd(data)
    assert 'macd' in result.columns
    assert 'signal' in result.columns
    assert 'hist' in result.columns


def test_calculate_rsi():
    """测试RSI计算"""
    data = pd.DataFrame({
        'close': np.random.rand(30) * 100 + 100
    })
    result = calculate_rsi(data)
    assert all(0 <= r <= 100 for r in result.dropna())

def test_calculate_rsi_different_periods():
    """测试不同周期的RSI计算"""
    data = pd.DataFrame({
        'close': np.random.rand(50) * 100 + 100
    })
    for period in [6, 9, 14, 20]:
        result = calculate_rsi(data, period=period)
        assert all(0 <= r <= 100 for r in result.dropna())

def test_calculate_rsi_all_gains():
    """测试连续上涨时的RSI边界情况（无除零错误）"""
    data = pd.DataFrame({
        'close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115]
    })
    result = calculate_rsi(data, period=14)
    assert not pd.isna(result.iloc[-1])
    assert result.iloc[-1] > 90  # 连续上涨RSI应接近100


def test_calculate_kdj():
    """测试KDJ计算"""
    data = pd.DataFrame({
        'high': np.random.rand(30) * 10 + 100,
        'low': np.random.rand(30) * 10 + 90,
        'close': np.random.rand(30) * 10 + 95
    })
    result = calculate_kdj(data)
    assert 'k' in result.columns
    assert 'd' in result.columns
    assert 'j' in result.columns
