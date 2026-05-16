import pandas as pd
import numpy as np
from indicators import calculate_ma, calculate_boll, calculate_macd, calculate_rsi, calculate_kdj


def test_calculate_ma():
    """测试均线计算"""
    data = pd.DataFrame({
        'close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
    })
    result = calculate_ma(data, period=5)
    assert 'ma5' in result.columns
    assert not pd.isna(result['ma5'].iloc[4])


def test_calculate_boll():
    """测试布林带计算"""
    data = pd.DataFrame({
        'close': np.random.rand(50) * 100 + 100
    })
    result = calculate_boll(data)
    assert 'boll_upper' in result.columns
    assert 'boll_middle' in result.columns
    assert 'boll_lower' in result.columns


def test_calculate_macd():
    """测试MACD计算"""
    data = pd.DataFrame({
        'close': np.random.rand(50) * 100 + 100
    })
    result = calculate_macd(data)
    assert 'macd' in result.columns
    assert 'macd_signal' in result.columns
    assert 'macd_hist' in result.columns


def test_calculate_rsi():
    """测试RSI计算"""
    data = pd.DataFrame({
        'close': np.random.rand(30) * 100 + 100
    })
    result = calculate_rsi(data)
    assert 'rsi' in result.columns
    assert all(0 <= r <= 100 for r in result['rsi'].dropna())


def test_calculate_kdj():
    """测试KDJ计算"""
    data = pd.DataFrame({
        'high': np.random.rand(30) * 10 + 100,
        'low': np.random.rand(30) * 10 + 90,
        'close': np.random.rand(30) * 10 + 95
    })
    result = calculate_kdj(data)
    assert 'kdj_k' in result.columns
    assert 'kdj_d' in result.columns
    assert 'kdj_j' in result.columns
