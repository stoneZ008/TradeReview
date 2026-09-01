import pandas as pd

from strategies import TradingStrategy, TrendDetector


# ========================================
# 新增买入策略
# ========================================


class TurtleBreakout(TradingStrategy):
    """
    海龟突破买入策略
    条件: 价格突破N日最高价，放量收阳
    """

    def __init__(self, weight=1.2, lookback=20, vol_ratio=1.5):
        super().__init__("海龟突破", weight, strategy_type="buy")
        self.lookback = lookback
        self.vol_ratio = vol_ratio

    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        if len(df) < self.lookback + 1:
            return signals

        n_high = df["high"].rolling(window=self.lookback).max().shift(1)
        breakout = df["close"] > n_high
        vol_ok = df["vol_ratio"] >= self.vol_ratio
        yang = df["close"] > df["open"]
        signals[breakout & vol_ok & yang] = 1
        return signals


class MABullishAlignment(TradingStrategy):
    """
    均线多头排列买入策略
    条件: MA5>MA10>MA20>MA60 多头排列刚确认，收盘在MA5上方，收阳
    """

    def __init__(self, weight=1.3):
        super().__init__("均线多头排列", weight, strategy_type="buy")

    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)

        aligned = (
            (df["ma5"] > df["ma10"])
            & (df["ma10"] > df["ma20"])
            & (df["ma20"] > df["ma60"])
            & df["ma60"].notna()
        )
        prev_aligned = aligned.shift(1, fill_value=False)
        just_formed = aligned & ~prev_aligned
        above_ma5 = df["close"] > df["ma5"]
        yang = df["close"] > df["open"]
        signals[just_formed & above_ma5 & yang] = 1
        return signals


class GapFillBuy(TradingStrategy):
    """
    缺口回补买入策略
    条件: 跳空高开后盘中回补缺口，收盘回升收阳（支撑有效）
    """

    def __init__(self, weight=1.0):
        super().__init__("缺口回补买入", weight, strategy_type="buy")

    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)

        gap_up = df["open"] > df["high"].shift(1)
        fill_gap = df["low"] <= df["high"].shift(1)
        recover = df["close"] > df["open"]
        above_prev = df["close"] > df["close"].shift(1)
        signals[gap_up & fill_gap & recover & above_prev] = 1
        return signals


class VolumePriceRise(TradingStrategy):
    """
    量价齐升买入策略
    条件: 连续N日放量上涨，MACD柱状图为正
    """

    def __init__(self, weight=1.1, days=2, vol_ratio=1.2):
        super().__init__("量价齐升", weight, strategy_type="buy")
        self.days = days
        self.vol_ratio = vol_ratio

    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        if len(df) < self.days + 1:
            return signals

        vol_ok = df["vol_ratio"] >= self.vol_ratio
        price_up = df["close"] > df["close"].shift(1)
        macd_pos = df["macd_hist"] > 0

        consec_vol = vol_ok.rolling(window=self.days).sum() == self.days
        consec_up = price_up.rolling(window=self.days).sum() == self.days

        signals[consec_vol & consec_up & macd_pos] = 1
        return signals


# ========================================
# 新增卖出策略
# ========================================


class TurtleBreakdown(TradingStrategy):
    """
    海龟跌破卖出策略
    条件: 价格跌破N日最低价，收阴
    """

    def __init__(self, weight=1.2, lookback=10):
        super().__init__("海龟跌破", weight, strategy_type="sell")
        self.lookback = lookback

    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        if len(df) < self.lookback + 1:
            return signals

        n_low = df["low"].rolling(window=self.lookback).min().shift(1)
        breakdown = df["close"] < n_low
        yin = df["close"] < df["open"]
        signals[breakdown & yin] = -1
        return signals


class MABearishAlignment(TradingStrategy):
    """
    均线空头排列卖出策略
    条件: MA5<MA10<MA20 空头排列刚形成，收盘在MA20下方，收阴
    """

    def __init__(self, weight=1.3):
        super().__init__("均线空头排列", weight, strategy_type="sell")

    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)

        aligned = (df["ma5"] < df["ma10"]) & (df["ma10"] < df["ma20"])
        prev_aligned = aligned.shift(1, fill_value=False)
        just_formed = aligned & ~prev_aligned
        below_ma20 = df["close"] < df["ma20"]
        yin = df["close"] < df["open"]
        signals[just_formed & below_ma20 & yin] = -1
        return signals


class VolumePriceDivergence(TradingStrategy):
    """
    量价背离卖出策略
    条件: 价格创近N日新高但成交量萎缩，RSI处于高位（顶背离）
    """

    def __init__(self, weight=1.1, lookback=20, rsi_threshold=65):
        super().__init__("量价背离", weight, strategy_type="sell")
        self.lookback = lookback
        self.rsi_threshold = rsi_threshold

    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        if len(df) < self.lookback + 1:
            return signals

        n_high = df["high"].rolling(window=self.lookback).max()
        new_high = df["high"] >= n_high
        vol_shrink = df["vol_ratio"] < 0.8
        rsi_high = df["rsi"] > self.rsi_threshold
        signals[new_high & vol_shrink & rsi_high] = -1
        return signals


class GapFillSell(TradingStrategy):
    """
    跳空低开卖出策略
    条件: 跳空低开后反弹乏力收阴，收盘低于前日最低
    """

    def __init__(self, weight=1.0):
        super().__init__("跳空低开卖出", weight, strategy_type="sell")

    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)

        gap_down = df["open"] < df["low"].shift(1)
        weak = df["close"] < df["open"]
        below_prev = df["close"] < df["low"].shift(1)
        signals[gap_down & weak & below_prev] = -1
        return signals


# ========================================
# 策略注册表
# ========================================

# 每个策略的元信息：key, 类, 中文名, 类型, 默认权重, 可调参数, 是否空头趋势下允许
# 参数定义格式: {key, label, type, default, min, max, step, options}
_STRATEGY_SPECS = []


def _spec(key, cls, name, stype, default_weight, params=None, bearish_allowed=False):
    _STRATEGY_SPECS.append(
        {
            "key": key,
            "class": cls,
            "name": name,
            "type": stype,
            "default_weight": default_weight,
            "params": params or [],
            "bearish_allowed": bearish_allowed,
        }
    )


# --- 买入策略（复用现有 + 新增）---
from strategies import (  # noqa: E402
    MACDGoldenCross,
    BOLLSupport,
    MA20Support,
    VolumeBreakout,
    RSIOversold,
    KDJGoldenCross,
    BottomReversal,
    MACDDeathCross,
    BOLLResistance,
    PriceBelowMA20,
    BreakPreviousLow,
    ConsecutiveDecline,
    RSIOverbought,
    KDJDeathCross,
)

_spec("macd_golden_cross", MACDGoldenCross, "MACD金叉", "buy", 1.5, bearish_allowed=False)
_spec("boll_support", BOLLSupport, "布林带下轨支撑", "buy", 1.2, bearish_allowed=True)
_spec("ma20_support", MA20Support, "MA20支撑", "buy", 1.2)
_spec("volume_breakout", VolumeBreakout, "放量突破", "buy", 1.0, params=[
    {"key": "ratio", "label": "量比阈值", "type": "number", "default": 2.0, "min": 1.0, "max": 5.0, "step": 0.1}
])
_spec("rsi_oversold", RSIOversold, "RSI超卖", "buy", 1.0, bearish_allowed=True, params=[
    {"key": "threshold", "label": "RSI超卖阈值", "type": "number", "default": 30, "min": 15, "max": 40, "step": 1}
])
_spec("kdj_golden_cross", KDJGoldenCross, "KDJ金叉", "buy", 1.0, bearish_allowed=True, params=[
    {"key": "threshold", "label": "K超卖阈值", "type": "number", "default": 30, "min": 10, "max": 50, "step": 1}
])
_spec("bottom_reversal", BottomReversal, "底部反转", "buy", 1.5, bearish_allowed=True, params=[
    {"key": "lookback", "label": "回溯天数", "type": "number", "default": 10, "min": 5, "max": 30, "step": 1}
])
_spec("turtle_breakout", TurtleBreakout, "海龟突破", "buy", 1.2, params=[
    {"key": "lookback", "label": "突破周期", "type": "number", "default": 20, "min": 5, "max": 60, "step": 1},
    {"key": "vol_ratio", "label": "量比阈值", "type": "number", "default": 1.5, "min": 1.0, "max": 5.0, "step": 0.1}
])
_spec("ma_bullish_alignment", MABullishAlignment, "均线多头排列", "buy", 1.3)
_spec("gap_fill_buy", GapFillBuy, "缺口回补买入", "buy", 1.0)
_spec("volume_price_rise", VolumePriceRise, "量价齐升", "buy", 1.1, params=[
    {"key": "days", "label": "连续天数", "type": "number", "default": 2, "min": 2, "max": 5, "step": 1},
    {"key": "vol_ratio", "label": "量比阈值", "type": "number", "default": 1.2, "min": 1.0, "max": 3.0, "step": 0.1}
])

# --- 卖出策略（复用现有 + 新增）---
_spec("macd_death_cross", MACDDeathCross, "MACD死叉", "sell", 1.5)
_spec("boll_resistance", BOLLResistance, "布林带上轨压力", "sell", 1.2)
_spec("price_below_ma20", PriceBelowMA20, "跌破MA20", "sell", 1.5)
_spec("break_previous_low", BreakPreviousLow, "跌破前低", "sell", 1.0, params=[
    {"key": "lookback_days", "label": "回溯天数", "type": "number", "default": 5, "min": 3, "max": 20, "step": 1}
])
_spec("consecutive_decline", ConsecutiveDecline, "连续下跌", "sell", 1.0, params=[
    {"key": "days", "label": "连续天数", "type": "number", "default": 3, "min": 2, "max": 10, "step": 1},
    {"key": "decline_threshold", "label": "跌幅阈值", "type": "number", "default": 0.05, "min": 0.02, "max": 0.20, "step": 0.01}
])
_spec("rsi_overbought", RSIOverbought, "RSI超买", "sell", 1.0, params=[
    {"key": "threshold", "label": "RSI超买阈值", "type": "number", "default": 70, "min": 60, "max": 85, "step": 1}
])
_spec("kdj_death_cross", KDJDeathCross, "KDJ死叉", "sell", 1.0, params=[
    {"key": "threshold", "label": "J超买阈值", "type": "number", "default": 100, "min": 80, "max": 120, "step": 1}
])
_spec("turtle_breakdown", TurtleBreakdown, "海龟跌破", "sell", 1.2, params=[
    {"key": "lookback", "label": "跌破周期", "type": "number", "default": 10, "min": 5, "max": 30, "step": 1}
])
_spec("ma_bearish_alignment", MABearishAlignment, "均线空头排列", "sell", 1.3)
_spec("volume_price_divergence", VolumePriceDivergence, "量价背离", "sell", 1.1, params=[
    {"key": "lookback", "label": "回溯周期", "type": "number", "default": 20, "min": 10, "max": 60, "step": 1},
    {"key": "rsi_threshold", "label": "RSI高位阈值", "type": "number", "default": 65, "min": 55, "max": 80, "step": 1}
])
_spec("gap_fill_sell", GapFillSell, "跳空低开卖出", "sell", 1.0)


def get_strategy_templates():
    """返回所有策略模板（用于前端渲染配置面板）"""
    templates = []
    for spec in _STRATEGY_SPECS:
        templates.append(
            {
                "key": spec["key"],
                "name": spec["name"],
                "type": spec["type"],
                "default_weight": spec["default_weight"],
                "bearish_allowed": spec["bearish_allowed"],
                "params": spec["params"],
            }
        )
    return templates


def _spec_map():
    return {s["key"]: s for s in _STRATEGY_SPECS}


def _build_strategy(spec, weight, params):
    """根据 spec 和参数构造策略实例"""
    cls = spec["class"]
    param_keys = {p["key"] for p in spec["params"]}
    kwargs = {}
    for k, v in (params or {}).items():
        if k in param_keys:
            kwargs[k] = v
    return cls(weight=weight, **kwargs)


def get_default_config():
    """返回默认策略配置（启用所有策略，使用默认权重和参数）"""
    spec_map = _spec_map()
    strategies = {}
    for spec in _STRATEGY_SPECS:
        params = {p["key"]: p["default"] for p in spec["params"]}
        strategies[spec["key"]] = {
            "enabled": True,
            "weight": spec["default_weight"],
            "params": params,
        }
    return {
        "buy_threshold": 0.08,
        "sell_threshold": 0.08,
        "strategies": strategies,
    }


def _preset_config(buy_threshold, sell_threshold, enabled_list):
    """根据启用的策略列表构建预设配置

    enabled_list: [(key, weight), ...] 或 [(key, weight, params_dict), ...]
    未列出的策略自动禁用
    """
    config = get_default_config()
    config["buy_threshold"] = buy_threshold
    config["sell_threshold"] = sell_threshold
    enabled_keys = set()
    for item in enabled_list:
        key = item[0]
        weight = item[1] if len(item) > 1 else None
        params = item[2] if len(item) > 2 else None
        enabled_keys.add(key)
        if key in config["strategies"]:
            config["strategies"][key]["enabled"] = True
            if weight is not None:
                config["strategies"][key]["weight"] = weight
            if params:
                config["strategies"][key]["params"].update(params)
    for key in config["strategies"]:
        if key not in enabled_keys:
            config["strategies"][key]["enabled"] = False
    return config


_PRESETS = None


def _build_presets():
    global _PRESETS
    if _PRESETS is not None:
        return _PRESETS

    presets = [
        {
            "key": "conservative",
            "name": "保守稳健",
            "description": "高阈值少信号，只保留最可靠的指标，适合震荡市",
            "config": _preset_config(
                buy_threshold=0.15,
                sell_threshold=0.12,
                enabled_list=[
                    ("macd_golden_cross", 1.8),
                    ("ma20_support", 1.5),
                    ("rsi_oversold", 1.0),
                    ("volume_breakout", 1.2),
                    ("macd_death_cross", 1.8),
                    ("price_below_ma20", 1.5),
                    ("break_previous_low", 1.2),
                    ("boll_resistance", 1.2),
                ],
            ),
        },
        {
            "key": "balanced",
            "name": "均衡配置",
            "description": "全策略启用，默认权重，适合大多数场景",
            "config": get_default_config(),
        },
        {
            "key": "aggressive",
            "name": "激进进取",
            "description": "低阈值多信号，提升反弹/突破类权重，适合短线",
            "config": _preset_config(
                buy_threshold=0.05,
                sell_threshold=0.05,
                enabled_list=[
                    ("macd_golden_cross", 1.5),
                    ("boll_support", 1.5),
                    ("ma20_support", 1.0),
                    ("volume_breakout", 1.5),
                    ("rsi_oversold", 1.5),
                    ("kdj_golden_cross", 1.5),
                    ("bottom_reversal", 2.0),
                    ("turtle_breakout", 1.5),
                    ("gap_fill_buy", 1.2),
                    ("volume_price_rise", 1.2),
                    ("macd_death_cross", 1.2),
                    ("boll_resistance", 1.0),
                    ("price_below_ma20", 1.2),
                    ("rsi_overbought", 1.5),
                    ("kdj_death_cross", 1.2),
                    ("turtle_breakdown", 1.2),
                    ("volume_price_divergence", 1.2),
                ],
            ),
        },
        {
            "key": "trend_following",
            "name": "趋势跟踪",
            "description": "侧重均线/突破/MACD，屏蔽超卖反弹，适合单边行情",
            "config": _preset_config(
                buy_threshold=0.08,
                sell_threshold=0.10,
                enabled_list=[
                    ("ma_bullish_alignment", 2.0),
                    ("turtle_breakout", 1.8),
                    ("macd_golden_cross", 1.5),
                    ("volume_price_rise", 1.5),
                    ("ma20_support", 1.2),
                    ("boll_support", 1.0),
                    ("ma_bearish_alignment", 2.0),
                    ("turtle_breakdown", 1.8),
                    ("macd_death_cross", 1.5),
                    ("price_below_ma20", 1.5),
                    ("consecutive_decline", 1.2),
                    ("break_previous_low", 1.0),
                ],
            ),
        },
        {
            "key": "contrarian",
            "name": "超跌反弹",
            "description": "侧重RSI/KDJ/布林下轨/底部反转，适合抄底",
            "config": _preset_config(
                buy_threshold=0.06,
                sell_threshold=0.10,
                enabled_list=[
                    ("rsi_oversold", 2.0, {"threshold": 35}),
                    ("kdj_golden_cross", 2.0, {"threshold": 35}),
                    ("boll_support", 2.0),
                    ("bottom_reversal", 2.0),
                    ("gap_fill_buy", 1.5),
                    ("ma20_support", 1.0),
                    ("rsi_overbought", 1.5, {"threshold": 65}),
                    ("kdj_death_cross", 1.5),
                    ("boll_resistance", 1.5),
                    ("volume_price_divergence", 1.5, {"rsi_threshold": 60}),
                    ("macd_death_cross", 1.0),
                ],
            ),
        },
    ]
    _PRESETS = presets
    return presets


def get_preset_configs():
    """返回所有预设方案"""
    return [
        {"key": p["key"], "name": p["name"], "description": p["description"]}
        for p in _build_presets()
    ]


def get_preset_config(key):
    """返回指定预设方案的完整配置"""
    for p in _build_presets():
        if p["key"] == key:
            return p["config"]
    return None


# ========================================
# 可配置复合策略
# ========================================


class ConfigurableCompositeStrategy:
    """
    可配置复合策略：根据用户配置的策略集合、权重、参数生成信号
    """

    def __init__(self, config=None):
        self.config = config or get_default_config()
        self.buy_threshold = self.config.get("buy_threshold", 0.08)
        self.sell_threshold = self.config.get("sell_threshold", 0.08)
        self.trend_detector = TrendDetector()
        self.spec_map = _spec_map()

    def _build_strategies(self):
        strategies = []
        total_buy_weight = 0.0
        total_sell_weight = 0.0
        strat_config = self.config.get("strategies", {})

        for key, cfg in strat_config.items():
            if not cfg.get("enabled", True):
                continue
            spec = self.spec_map.get(key)
            if spec is None:
                continue
            weight = cfg.get("weight", spec["default_weight"])
            params = cfg.get("params", {})
            strategy = _build_strategy(spec, weight, params)
            strategies.append((strategy, spec))
            if spec["type"] == "buy":
                total_buy_weight += weight
            else:
                total_sell_weight += weight

        # 防止除零
        if total_buy_weight == 0:
            total_buy_weight = 1.0
        if total_sell_weight == 0:
            total_sell_weight = 1.0

        return strategies, total_buy_weight, total_sell_weight

    def generate_signals(self, df):
        """
        综合多个策略生成加权信号
        返回: DataFrame with buy_score, sell_score, signal, trend, composite_score
        """
        trend = self.trend_detector.generate_trend(df)

        buy_score = pd.Series(0.0, index=df.index)
        sell_score = pd.Series(0.0, index=df.index)

        strategies, total_buy_w, total_sell_w = self._build_strategies()

        for strategy, spec in strategies:
            signals = strategy.generate_signals(df)

            # 趋势过滤
            if strategy.strategy_type == "buy":
                if spec["bearish_allowed"]:
                    # 超跌反弹策略：在所有趋势下生效（空头趋势下权重打折）
                    trend_weight = trend.map({1: 1.0, 0: 1.0, -1: 0.7})
                    signals = signals * trend_weight
                else:
                    # 其他买入策略：只在多头趋势或震荡中有效
                    signals = signals * (trend >= 0)
            elif strategy.strategy_type == "sell":
                # 卖出策略：只在空头趋势或震荡中有效
                signals = signals * (trend <= 0)

            buy_score += signals.clip(lower=0) * strategy.weight
            sell_score += (-signals).clip(lower=0) * strategy.weight

        # 归一化
        buy_score = buy_score / total_buy_w
        sell_score = sell_score / total_sell_w

        # 生成最终信号
        final_signal = pd.Series(0, index=df.index)
        final_signal[buy_score >= self.buy_threshold] = 1
        final_signal[sell_score >= self.sell_threshold] = -1

        # 连续卖出过滤（复用现有逻辑）
        consecutive_sell_count = 0
        last_buy_idx = -1
        last_sell_idx = -1

        for i in range(len(final_signal)):
            if final_signal.iloc[i] == 1:
                consecutive_sell_count = 0
                last_buy_idx = i
                last_sell_idx = -1
            elif final_signal.iloc[i] == -1:
                consecutive_sell_count += 1
                days_since_buy = i - last_buy_idx if last_buy_idx >= 0 else i + 1
                days_since_last_sell = i - last_sell_idx if last_sell_idx >= 0 else i + 1

                if (consecutive_sell_count >= 3 and days_since_buy > 10) or (
                    consecutive_sell_count >= 2 and days_since_last_sell < 5
                ):
                    final_signal.iloc[i] = 0
                else:
                    last_sell_idx = i

        return pd.DataFrame(
            {
                "buy_score": buy_score,
                "sell_score": sell_score,
                "signal": final_signal,
                "trend": trend,
                "composite_score": buy_score - sell_score,
            },
            index=df.index,
        )


def generate_custom_signals(df, config=None):
    """
    用自定义配置生成交易信号

    Parameters:
        df: 包含技术指标的DataFrame
        config: 策略配置（含 buy_threshold, sell_threshold, strategies）

    Returns:
        DataFrame with buy_score, sell_score, signal, trend, composite_score
    """
    if config is None:
        config = get_default_config()

    composite = ConfigurableCompositeStrategy(config=config)
    return composite.generate_signals(df)
