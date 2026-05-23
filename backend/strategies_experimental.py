import pandas as pd

from strategies import TradingStrategy, TrendDetector
from volatility import classify_volatility


class MACDGoldenCrossV2(TradingStrategy):
    def __init__(self, weight=1.5, zero_filter="strict"):
        super().__init__("MACD金叉买入V2", weight, "buy")
        self.zero_filter = zero_filter

    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        cross = (df["macd"] > df["macd_signal"]) & (df["macd"].shift(1) <= df["macd_signal"].shift(1))
        if self.zero_filter == "off":
            zero_ok = pd.Series(True, index=df.index)
        elif self.zero_filter == "near":
            zero_ok = df["macd"] > -df["close"] * 0.03
        else:
            zero_ok = df["macd"] > 0
        signals[cross & (df["macd_hist"] > 0) & zero_ok] = 1
        return signals


class BOLLSupportV2(TradingStrategy):
    def __init__(self, weight=1.2, factor=1.0):
        super().__init__("布林带下轨支撑V2", weight, "buy")
        self.factor = factor

    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        signals[
            (df["low"].shift(1) <= df["boll_lower"].shift(1) * self.factor)
            & (df["close"] > df["boll_lower"])
            & (df["close"] > df["open"])
        ] = 1
        return signals


class MA20SupportV2(TradingStrategy):
    def __init__(self, weight=1.2, deviation=0.01):
        super().__init__("MA20支撑V2", weight, "buy")
        self.deviation = deviation

    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        prev_near = abs(df["close"].shift(1) - df["ma20"].shift(1)) / df["ma20"].shift(1) < self.deviation
        reclaim = (df["close"].shift(1) < df["ma20"].shift(1)) & (df["close"] >= df["ma20"])
        signals[(prev_near | reclaim) & (df["close"] > df["close"].shift(1)) & (df["close"] > df["open"])] = 1
        return signals


class VolumeBreakoutV2(TradingStrategy):
    def __init__(self, weight=1.0, ratio=2.0):
        super().__init__("放量突破V2", weight, "buy")
        self.ratio = ratio

    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        signals[(df["vol_ratio"] >= self.ratio) & (df["close"] > df["high"].shift(1)) & (df["close"] > df["open"])] = 1
        return signals


class RSIOversoldV2(TradingStrategy):
    def __init__(self, weight=1.0, threshold=30):
        super().__init__("RSI超卖V2", weight, "buy")
        self.threshold = threshold

    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        signals[
            (df["rsi"].shift(1) < self.threshold) & (df["rsi"] > df["rsi"].shift(1)) & (df["rsi"] < self.threshold + 8)
        ] = 1
        return signals


class KDJGoldenCrossV2(TradingStrategy):
    def __init__(self, weight=1.0, threshold=30):
        super().__init__("KDJ金叉V2", weight, "buy")
        self.threshold = threshold

    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        cross = (df["kdj_k"] > df["kdj_d"]) & (df["kdj_k"].shift(1) <= df["kdj_d"].shift(1))
        signals[cross & (df["kdj_k"].shift(1) < self.threshold)] = 1
        return signals


class PullbackReversalV2(TradingStrategy):
    def __init__(self, weight=1.4, lookback=10, min_pullback=0.05):
        super().__init__("回调结束反弹V2", weight, "buy")
        self.lookback = lookback
        self.min_pullback = min_pullback

    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        for i in range(self.lookback, len(df)):
            recent_high = df["high"].iloc[i - self.lookback : i].max()
            recent_low = df["low"].iloc[i - self.lookback : i + 1].min()
            pullback = (recent_high - recent_low) / recent_high if recent_high > 0 else 0
            if (
                pullback >= self.min_pullback
                and df["close"].iloc[i] > df["open"].iloc[i]
                and df["close"].iloc[i] > df["close"].iloc[i - 1]
                and (df["macd_hist"].iloc[i] > df["macd_hist"].iloc[i - 1] or df["rsi"].iloc[i] > df["rsi"].iloc[i - 1])
            ):
                signals.iloc[i] = 1
        return signals


class TrendPullbackRestartV2(TradingStrategy):
    def __init__(self, weight=1.2, lookback=5):
        super().__init__("趋势回踩后二次启动V2", weight, "buy")
        self.lookback = lookback

    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        for i in range(max(self.lookback, 20), len(df)):
            prev_high = df["high"].iloc[i - self.lookback : i].max()
            had_pullback = df["close"].iloc[i - 1] < df["ma5"].iloc[i - 1]
            trend_ok = df["ma5"].iloc[i] >= df["ma10"].iloc[i] and df["close"].iloc[i] > df["ma20"].iloc[i]
            restart = df["close"].iloc[i] > prev_high and df["close"].iloc[i] > df["open"].iloc[i]
            momentum_ok = (
                df["macd_hist"].iloc[i] > df["macd_hist"].iloc[i - 1] or df["rsi"].iloc[i] > df["rsi"].iloc[i - 1]
            )
            if had_pullback and trend_ok and restart and momentum_ok:
                signals.iloc[i] = 1
        return signals


class BottomReversalV2(TradingStrategy):
    def __init__(self, weight=1.5, lookback=10, ratio=1.5, rsi_threshold=40):
        super().__init__("底部反转V2", weight, "buy")
        self.lookback = lookback
        self.ratio = ratio
        self.rsi_threshold = rsi_threshold

    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        for i in range(self.lookback, len(df)):
            window = df["low"].iloc[i - self.lookback : i + 1]
            near_bottom = (
                window.reset_index(drop=True).idxmin() >= len(window) - 4 or df["low"].iloc[i] <= window.min() * 1.03
            )
            ok = (
                near_bottom
                and df["close"].iloc[i] > df["open"].iloc[i]
                and df["close"].iloc[i] > df["close"].iloc[i - 1]
            )
            improve = df["macd_hist"].iloc[i] > df["macd_hist"].iloc[i - 1] or (
                df["rsi"].iloc[i] < self.rsi_threshold and df["rsi"].iloc[i] > df["rsi"].iloc[i - 1]
            )
            if ok and improve and df["vol_ratio"].iloc[i] >= self.ratio:
                signals.iloc[i] = 1
        return signals


class MACDDeathCrossV2(TradingStrategy):
    def __init__(self, weight=1.5, zero_filter="strict"):
        super().__init__("MACD死叉卖出V2", weight, "sell")
        self.zero_filter = zero_filter

    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        cross = (df["macd"] < df["macd_signal"]) & (df["macd"].shift(1) >= df["macd_signal"].shift(1))
        zero_ok = df["macd"] > 0 if self.zero_filter == "strict" else df["macd"] > -df["close"] * 0.02
        signals[cross & zero_ok] = -1
        return signals


class BOLLResistanceV2(TradingStrategy):
    def __init__(self, weight=1.2, factor=1.0):
        super().__init__("布林带上轨压力V2", weight, "sell")
        self.factor = factor

    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        signals[
            (df["high"].shift(1) >= df["boll_upper"].shift(1) / self.factor)
            & (df["close"] < df["boll_upper"])
            & ((df["close"] - df["open"]) / df["open"] < -0.03)
        ] = -1
        return signals


class PriceBelowMA20V2(TradingStrategy):
    def __init__(self, weight=1.5, deviation=0.01):
        super().__init__("跌破MA20V2", weight, "sell")
        self.deviation = deviation

    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        signals[
            (df["close"].shift(1) >= df["ma20"].shift(1) * (1 - self.deviation))
            & (df["close"] < df["ma20"] * (1 - self.deviation))
            & (df["close"] < df["open"])
        ] = -1
        return signals


class BreakPreviousLowV2(TradingStrategy):
    def __init__(self, weight=1.0, lookback_days=5):
        super().__init__("跌破前低V2", weight, "sell")
        self.lookback_days = lookback_days

    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        for i in range(self.lookback_days, len(df)):
            if df["close"].iloc[i] < df["low"].iloc[i - self.lookback_days : i].min():
                signals.iloc[i] = -1
        return signals


class ConsecutiveDeclineV2(TradingStrategy):
    def __init__(self, weight=1.0, days=3, decline_threshold=0.05):
        super().__init__("连续下跌V2", weight, "sell")
        self.days = days
        self.decline_threshold = decline_threshold

    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        for i in range(self.days, len(df)):
            total_decline = (df["close"].iloc[i] - df["close"].iloc[i - self.days]) / df["close"].iloc[i - self.days]
            if total_decline < -self.decline_threshold:
                signals.iloc[i] = -1
        return signals


class RSIOverboughtV2(TradingStrategy):
    def __init__(self, weight=1.0, threshold=70):
        super().__init__("RSI超买V2", weight, "sell")
        self.threshold = threshold

    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        signals[
            (df["rsi"].shift(1) > self.threshold) & (df["rsi"] < df["rsi"].shift(1)) & (df["rsi"] > self.threshold - 5)
        ] = -1
        return signals


class KDJDeathCrossV2(TradingStrategy):
    def __init__(self, weight=1.0, threshold=100):
        super().__init__("KDJ死叉V2", weight, "sell")
        self.threshold = threshold

    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        death_cross = (df["kdj_k"] < df["kdj_d"]) & (df["kdj_k"].shift(1) >= df["kdj_d"].shift(1))
        signals[death_cross & (df["kdj_j"] > self.threshold)] = -1
        return signals


class CompositeStrategyV2:
    def __init__(self, params=None, buy_threshold=0.08, sell_threshold=0.08):
        self.params = params or {}
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.trend_detector = TrendDetector()
        self.strategies = self._default_strategies()

    def _default_strategies(self):
        p = self.params
        return [
            MACDGoldenCrossV2(1.5, p.get("macd_zero_filter", "strict")),
            BOLLSupportV2(1.2, p.get("boll_touch_factor", 1.0)),
            MA20SupportV2(1.2, p.get("ma20_deviation", 0.01)),
            VolumeBreakoutV2(1.0, p.get("vol_breakout_ratio", 2.0)),
            RSIOversoldV2(1.0, p.get("rsi_oversold", 30)),
            KDJGoldenCrossV2(1.0, p.get("kdj_k_threshold", 30)),
            BottomReversalV2(
                1.5, ratio=p.get("bottom_reversal_ratio", 1.5), rsi_threshold=p.get("rsi_oversold", 30) + 10
            ),
            TrendPullbackRestartV2(1.2),
            MACDDeathCrossV2(1.5, p.get("macd_zero_filter", "strict")),
            BOLLResistanceV2(1.2, p.get("boll_touch_factor", 1.0)),
            PriceBelowMA20V2(1.5, p.get("ma20_deviation", 0.01)),
            BreakPreviousLowV2(1.0, 5),
            ConsecutiveDeclineV2(1.0, 3, p.get("consecutive_decline_threshold", 0.05)),
            RSIOverboughtV2(1.0, p.get("rsi_overbought", 70)),
            KDJDeathCrossV2(1.0, p.get("kdj_j_threshold", 100)),
        ]

    def generate_signals(self, df):
        trend = self.trend_detector.generate_trend(df)
        buy_score = pd.Series(0.0, index=df.index)
        sell_score = pd.Series(0.0, index=df.index)
        bearish_allowed = ["布林带下轨支撑V2", "RSI超卖V2", "KDJ金叉V2", "底部反转V2"]
        for strategy in self.strategies:
            signals = strategy.generate_signals(df)
            if strategy.strategy_type == "buy":
                if strategy.name in bearish_allowed:
                    signals = signals * trend.map({1: 1.0, 0: 1.0, -1: 0.8})
                else:
                    signals = signals * (trend >= 0)
            elif strategy.strategy_type == "sell":
                signals = signals * (trend <= 0)
            buy_score += signals.clip(lower=0) * strategy.weight
            sell_score += (-signals).clip(lower=0) * strategy.weight
        buy_score = buy_score / 10.6
        sell_score = sell_score / 8.7
        final_signal = pd.Series(0, index=df.index)
        overheated = (df["rsi"] >= 68) & (df["kdj_j"] >= 100)
        final_signal[(buy_score >= self.buy_threshold) & (~overheated)] = 1
        final_signal[sell_score >= self.sell_threshold] = -1
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


def generate_trading_signals_v2(df, config=None):
    if config is None:
        config = {"buy_threshold": 0.08, "sell_threshold": 0.08}
    volatility_info = classify_volatility(df)
    params = dict(volatility_info["params"])
    params.update(config.get("dynamic_params", {}))
    composite = CompositeStrategyV2(
        params=params,
        buy_threshold=config.get("buy_threshold", 0.08),
        sell_threshold=config.get("sell_threshold", 0.08),
    )
    signals = composite.generate_signals(df)
    signals.attrs["volatility_info"] = volatility_info
    return signals
