"""量价形态识别参数配置

所有阈值集中管理，便于调优。可通过传入 config 覆盖默认值。
"""

PATTERN_CONFIG = {
    # 形态一：放量突破 + 回踩缩量 → 真突破
    "true_breakout": {
        "breakout_vol_ratio": 1.5,       # 突破日量比 ≥ 此值
        "lookback_days": 10,              # 回看最近 N 天寻找突破日
        "resistance_window": 5,           # 突破前 N 日最高价为阻力位
        "pullback_vol_ratio": 0.8,        # 回踩日量比 < 此值视为缩量
        "pullback_vol_pct": 0.6,          # 或回踩日量 < 突破日量 × 此值
    },
    # 形态二：放量破位 → 止损信号
    "volume_breakdown": {
        "vol_ratio": 1.5,                 # 放量阈值
        "pct_change_threshold": -2.0,     # 破位跌幅阈值 %
        "support_window": 5,              # 前 N 日最低价为支撑
    },
    # 形态三：高位放量滞涨/下跌 → 危险信号
    "top_divergence": {
        "vol_ratio": 1.5,                 # 放量阈值
        "high_percentile": 80,            # 20 日收盘价分位 ≥ 此值视为高位
        "cumulative_return": 15.0,        # 近 20 日累计涨幅 > 此值视为高位
        "rsi_overbought": 70,             # RSI > 此值视为高位
        "stagnant_range": 1.0,            # 滞涨：|涨跌幅| < 此值
        "decline_threshold": -1.0,        # 下跌：涨跌幅 < 此值
        "turnover_threshold": 5.0,        # 换手率 > 此值则置信度加分
    },
}
