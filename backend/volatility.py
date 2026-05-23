import pandas as pd
import numpy as np


PARAMS_TABLE = {
    "high_vol": {
        "rsi_oversold": 40,
        "rsi_overbought": 60,
        "kdj_k_threshold": 40,
        "kdj_j_threshold": 85,
        "vol_breakout_ratio": 1.4,
        "bottom_reversal_ratio": 1.1,
        "ma20_deviation": 0.03,
        "boll_touch_factor": 1.02,
        "macd_zero_filter": "off",
        "consecutive_decline_threshold": 0.07,
    },
    "mid_vol": {
        "rsi_oversold": 35,
        "rsi_overbought": 65,
        "kdj_k_threshold": 35,
        "kdj_j_threshold": 95,
        "vol_breakout_ratio": 1.7,
        "bottom_reversal_ratio": 1.3,
        "ma20_deviation": 0.02,
        "boll_touch_factor": 1.01,
        "macd_zero_filter": "near",
        "consecutive_decline_threshold": 0.05,
    },
    "low_vol": {
        "rsi_oversold": 28,
        "rsi_overbought": 72,
        "kdj_k_threshold": 25,
        "kdj_j_threshold": 105,
        "vol_breakout_ratio": 2.2,
        "bottom_reversal_ratio": 1.6,
        "ma20_deviation": 0.01,
        "boll_touch_factor": 1.0,
        "macd_zero_filter": "strict",
        "consecutive_decline_threshold": 0.04,
    },
}


TIER_LABELS = {
    "high_vol": "小盘高波动",
    "mid_vol": "中盘中等波动",
    "low_vol": "大盘低波动",
}


def _calc_atr(df, period=14):
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low).abs(), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.rolling(window=period, min_periods=period).mean()


def classify_volatility(df):
    """
    按 ATR%（日均真实波幅占比）+ 60日成交额均值 划分波动率档位

    Returns:
        dict: {
            'tier': 'high_vol' | 'mid_vol' | 'low_vol',
            'tier_label': 中文标签,
            'atr_pct': float,
            'amount_ma60': float (元),
            'sample_size': int,
            'params': {...}
        }
    """
    sample_size = len(df)

    if sample_size < 60:
        tier = "mid_vol"
        return {
            "tier": tier,
            "tier_label": TIER_LABELS[tier] + "（数据不足，降级处理）",
            "atr_pct": None,
            "amount_ma60": None,
            "sample_size": sample_size,
            "params": PARAMS_TABLE[tier],
        }

    atr_series = _calc_atr(df, period=14)
    last_close = float(df["close"].iloc[-1])
    last_atr = float(atr_series.iloc[-1]) if not np.isnan(atr_series.iloc[-1]) else None
    atr_pct = (last_atr / last_close * 100) if (last_atr and last_close > 0) else None

    if "amount" in df.columns:
        amount_series = df["amount"]
        if amount_series.iloc[-30:].mean() < 1e6:
            amount_series = amount_series * 1e6
    else:
        amount_series = df["close"] * df["volume"]

    amount_ma60 = float(amount_series.rolling(window=60, min_periods=30).mean().iloc[-1])

    if atr_pct is None:
        tier = "mid_vol"
    elif atr_pct >= 4.0 or amount_ma60 < 3e8:
        tier = "high_vol"
    elif atr_pct < 2.5 and amount_ma60 >= 20e8:
        tier = "low_vol"
    else:
        tier = "mid_vol"

    return {
        "tier": tier,
        "tier_label": TIER_LABELS[tier],
        "atr_pct": round(atr_pct, 3) if atr_pct is not None else None,
        "amount_ma60": round(amount_ma60, 2),
        "sample_size": sample_size,
        "params": PARAMS_TABLE[tier],
    }
