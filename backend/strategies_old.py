import pandas as pd
import numpy as np

class TradingStrategy:
    """
    交易策略基类
    """
    def __init__(self, name, weight=1):
        self.name = name
        self.weight = weight
    
    def generate_signals(self, df):
        """
        生成信号，返回 Series: 1=买入, -1=卖出, 0=无信号
        """
        raise NotImplementedError

class MACDGoldenCross(TradingStrategy):
    """
    MACD金叉策略
    条件: MACD线上穿信号线，且MACD柱状图由负转正
    """
    def __init__(self, weight=1):
        super().__init__('MACD金叉', weight)
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        # MACD金叉: macd > signal 且前一日 macd <= signal
        golden_cross = (df['macd'] > df['macd_signal']) & \
                       (df['macd'].shift(1) <= df['macd_signal'].shift(1))
        
        # 柱状图为正或刚转正
        hist_positive = df['macd_hist'] > 0
        
        # 金叉且柱状图转正
        buy_signal = golden_cross & hist_positive
        signals[buy_signal] = 1
        
        return signals

class MACDDeathCross(TradingStrategy):
    """
    MACD死叉策略（优化版）
    - 主升浪中（MACD在零轴上方）减少卖出
    - 价格跌破MA20时才触发卖出
    """
    def __init__(self, weight=1):
        super().__init__('MACD死叉', weight)
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        death_cross = (df['macd'] < df['macd_signal']) & \
                      (df['macd'].shift(1) >= df['macd_signal'].shift(1))
        
        # 条件1: MACD在零轴下方的死叉（更可靠）
        below_zero = df['macd'] < 0
        
        # 条件2: 价格跌破MA20
        below_ma20 = df['close'] < df['ma20']
        
        # 条件3: 不是强势上涨趋势（MA5 < MA10 或 MA10 < MA20）
        not_strong_uptrend = (df['ma5'] < df['ma10']) | (df['ma10'] < df['ma20'])
        
        # 只有满足以下条件之一才卖出：MACD在零轴下，或价格跌破MA20，或趋势走弱
        sell_condition = death_cross & (below_zero | below_ma20 | not_strong_uptrend)
        
        signals[sell_condition] = -1
        
        return signals

class BOLLSupport(TradingStrategy):
    """
    布林带下轨支撑策略
    条件: 价格触及或跌破下轨后反弹
    """
    def __init__(self, weight=1):
        super().__init__('布林带下轨支撑', weight)
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        # 价格触及下轨后反弹
        touch_lower = df['low'] <= df['boll_lower']
        close_above_lower = df['close'] > df['boll_lower']
        prev_touch = df['low'].shift(1) <= df['boll_lower'].shift(1)
        
        # 前一天触及下轨，当天收盘回到下轨上方
        buy_signal = prev_touch & close_above_lower & (df['close'] > df['open'])
        signals[buy_signal] = 1
        
        return signals

class BOLLResistance(TradingStrategy):
    """
    布林带上轨压力策略（优化版）
    - 主升浪中价格可能沿上轨运行，不轻易卖出
    - 需要出现明显的反转信号才卖出
    """
    def __init__(self, weight=1):
        super().__init__('布林带上轨压力', weight)
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        # 价格触及上轨后回落
        touch_upper = df['high'] >= df['boll_upper']
        close_below_upper = df['close'] < df['boll_upper']
        
        # 需要连续2天触及上轨后回落（确认趋势结束）
        prev2_touch = df['high'].shift(2) >= df['boll_upper'].shift(2)
        prev_touch = df['high'].shift(1) >= df['boll_upper'].shift(1)
        
        # 同时出现大阴线（跌幅超过2%）才卖出
        big_yin = (df['close'] - df['open']) / df['open'] < -0.02
        
        # 或者MACD出现死叉
        macd_dead = (df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1))
        
        # 布林带收口（带宽变窄）+ 价格回落
        boll_narrow = df['boll_width'] < df['boll_width'].shift(1)
        
        # 卖出条件：触及上轨后回落 + (大阴线 或 MACD死叉) + 布林带收口
        sell_signal = prev_touch & close_below_upper & (big_yin | macd_dead) & boll_narrow
        signals[sell_signal] = -1
        
        return signals

class VolumeBreakout(TradingStrategy):
    """
    放量突破策略
    条件: 成交量是均量的2倍以上，且价格收阳
    """
    def __init__(self, weight=1, vol_ratio_threshold=2.0):
        super().__init__('放量突破', weight)
        self.threshold = vol_ratio_threshold
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        # 放量
        high_volume = df['vol_ratio'] >= self.threshold
        
        # 价格突破 - 收盘价突破前一日最高价
        price_break = df['close'] > df['high'].shift(1)
        
        # 阳线
        yang_candle = df['close'] > df['open']
        
        buy_signal = high_volume & price_break & yang_candle
        signals[buy_signal] = 1
        
        # 放量下跌 - 卖出信号
        price_drop = df['close'] < df['low'].shift(1)
        yin_candle = df['close'] < df['open']
        sell_signal = high_volume & price_drop & yin_candle
        signals[sell_signal] = -1
        
        return signals

class RSIOversold(TradingStrategy):
    """
    RSI超卖策略
    """
    def __init__(self, weight=1, oversold=30, overbought=70):
        super().__init__('RSI超买超卖', weight)
        self.oversold = oversold
        self.overbought = overbought
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        # RSI从超卖区回升
        was_oversold = df['rsi'].shift(1) < self.oversold
        now_rising = df['rsi'] > df['rsi'].shift(1)
        buy_signal = was_oversold & now_rising & (df['rsi'] < 50)
        signals[buy_signal] = 1
        
        # RSI从超买区回落
        was_overbought = df['rsi'].shift(1) > self.overbought
        now_falling = df['rsi'] < df['rsi'].shift(1)
        sell_signal = was_overbought & now_falling & (df['rsi'] > 50)
        signals[sell_signal] = -1
        
        return signals

class KDJGoldenCross(TradingStrategy):
    """
    KDJ金叉策略
    """
    def __init__(self, weight=1):
        super().__init__('KDJ金叉', weight)
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        # KDJ金叉
        golden_cross = (df['kdj_k'] > df['kdj_d']) & \
                       (df['kdj_k'].shift(1) <= df['kdj_d'].shift(1))
        
        # 在超卖区金叉更可靠
        oversold_cross = golden_cross & (df['kdj_k'] < 30)
        signals[oversold_cross] = 1
        
        # KDJ死叉
        death_cross = (df['kdj_k'] < df['kdj_d']) & \
                      (df['kdj_k'].shift(1) >= df['kdj_d'].shift(1))
        
        overbought_cross = death_cross & (df['kdj_k'] > 70)
        signals[overbought_cross] = -1
        
        return signals

class MACD背离(TradingStrategy):
    """
    MACD底背离策略: 价格创新低但MACD不创新低
    """
    def __init__(self, lookback=20, weight=1):
        super().__init__('MACD底背离', weight)
        self.lookback = lookback
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        for i in range(self.lookback, len(df)):
            # 查找局部最低点
            window_low = df['low'].iloc[i-self.lookback:i+1]
            window_macd_hist = df['macd_hist'].iloc[i-self.lookback:i+1]
            
            current_low = df['low'].iloc[i]
            min_idx = window_low.idxmin()
            
            if min_idx == df.index[i]:  # 当前是最低点
                # 检查是否有更早的低点
                earlier_lows = df['low'].iloc[max(0, i-self.lookback):i]
                if len(earlier_lows) > 0:
                    prev_min = earlier_lows.min()
                    if current_low < prev_min:
                        # 价格创新低
                        prev_min_idx = earlier_lows.idxmin()
                        # 但MACD柱状图没有创新低
                        prev_macd_hist_min = df['macd_hist'].loc[prev_min_idx]
                        if df['macd_hist'].iloc[i] > prev_macd_hist_min:
                            signals.iloc[i] = 1
        
        return signals

class MA20Support(TradingStrategy):
    """
    20日均线支撑策略
    """
    def __init__(self, weight=1):
        super().__init__('20日均线支撑', weight)
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        # 价格回踩20日线后反弹
        near_ma20 = abs(df['low'] - df['ma20']) / df['ma20'] < 0.01
        close_above_ma20 = df['close'] > df['ma20']
        prev_near = abs(df['low'].shift(1) - df['ma20'].shift(1)) / df['ma20'].shift(1) < 0.01
        
        buy_signal = prev_near & close_above_ma20 & (df['close'] > df['open'])
        signals[buy_signal] = 1
        
        return signals

class KLinePatternStrategy(TradingStrategy):
    """
    K线形态策略
    """
    def __init__(self, weight=1):
        super().__init__('K线形态', weight)
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        # 看涨信号
        bullish_patterns = ['看涨吞没', '早晨之星', '锤子线']
        for pattern in bullish_patterns:
            signals[df['candle_pattern'] == pattern] = 1
        
        # 看跌信号
        bearish_patterns = ['看跌吞没', '黄昏之星', '射击之星']
        for pattern in bearish_patterns:
            signals[df['candle_pattern'] == pattern] = -1
        
        return signals


class TrailingStopStrategy(TradingStrategy):
    """
    移动止盈策略（防卖飞）
    只有在明确的下跌趋势中才卖出，主升浪回调不卖
    """
    def __init__(self, weight=0.8, lookback=30, pullback_pct=0.20):
        super().__init__('移动止盈', weight)
        self.lookback = lookback  # 回看天数
        self.pullback_pct = pullback_pct  # 回撤比例（20%）
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        last_sell_idx = -999
        
        for i in range(self.lookback + 10, len(df)):
            recent_high = df['high'].iloc[i-self.lookback:i].max()
            current_close = df['close'].iloc[i]
            
            drawdown = (recent_high - current_close) / recent_high
            
            # 核心条件：回撤超过20%
            if drawdown < self.pullback_pct:
                continue
            
            # 条件1: 价格跌破MA60（中长期趋势走坏）
            below_ma60 = current_close < df['ma60'].iloc[i]
            
            # 条件2: MA20开始下降（20日均线拐头向下）
            ma20_falling = df['ma20'].iloc[i] < df['ma20'].iloc[i-5]
            
            # 条件3: MA5 < MA10 < MA20 空头排列
            ma_bear_align = (df['ma5'].iloc[i] < df['ma10'].iloc[i]) and \
                           (df['ma10'].iloc[i] < df['ma20'].iloc[i])
            
            # 条件4: 连续3天收阴
            if i < 3:
                continue
            consecutive_yin = all(df['close'].iloc[i-j] < df['open'].iloc[i-j] for j in range(3))
            
            # 必须满足：跌破MA60 + (MA20下降 或 空头排列) + 连续阴线
            if below_ma60 and (ma20_falling or ma_bear_align) and consecutive_yin:
                if i - last_sell_idx >= 15:  # 至少间隔15天
                    signals.iloc[i] = -1
                    last_sell_idx = i
        
        return signals


class TrendFilterStrategy(TradingStrategy):
    """
    趋势过滤策略
    强势上涨趋势中不卖出，弱势时才考虑卖出
    """
    def __init__(self, weight=1):
        super().__init__('趋势过滤', weight)
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        # 强势上涨条件
        strong_uptrend = (
            (df['ma5'] > df['ma10']) &  # MA5 > MA10
            (df['ma10'] > df['ma20']) &  # MA10 > MA20
            (df['close'] > df['ma5']) &  # 价格在MA5上方
            (df['macd'] > 0)  # MACD在零轴上方
        )
        
        # 弱势下跌条件
        weak_downtrend = (
            (df['ma5'] < df['ma10']) &  # MA5 < MA10
            (df['ma10'] < df['ma20']) &  # MA10 < MA20
            (df['close'] < df['ma20'])   # 价格在MA20下方
        )
        
        # 强势时不卖（信号为0），弱势时可以卖（信号为-1）
        # 这里我们通过给弱势情况下的卖出策略加分来实现
        
        return signals


class PriceBelowMA20(TradingStrategy):
    """
    价格跌破MA20策略（趋势反转信号）
    """
    def __init__(self, weight=1.5):
        super().__init__('跌破MA20', weight)
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        # 价格从MA20上方跌破到下方
        above_ma20 = df['close'].shift(1) >= df['ma20'].shift(1)
        below_ma20 = df['close'] < df['ma20']
        
        # 同时MA5下穿MA10（短期趋势转弱）
        ma_bearish = (df['ma5'] < df['ma10']) & (df['ma5'].shift(1) >= df['ma10'].shift(1))
        
        sell_signal = above_ma20 & below_ma20 & ma_bearish
        signals[sell_signal] = -1
        
        return signals


class ConsecutiveDecline(TradingStrategy):
    """
    连续下跌策略
    条件: 连续3天跌幅超过某个阈值
    """
    def __init__(self, weight=1, days=3, decline_threshold=0.05):
        super().__init__('连续下跌', weight)
        self.days = days  # 连续下跌天数
        self.decline_threshold = decline_threshold  # 跌幅阈值（5%）
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        for i in range(self.days, len(df)):
            # 计算连续N天的总跌幅
            start_close = df['close'].iloc[i - self.days]
            end_close = df['close'].iloc[i]
            
            # 总跌幅
            total_decline = (end_close - start_close) / start_close
            
            # 如果是下跌且超过阈值
            if total_decline < -self.decline_threshold:
                signals.iloc[i] = -1
        
        return signals

class BreakPreviousLow(TradingStrategy):
    """
    跌破前低策略
    条件: 收盘价跌破前N日的最低价
    """
    def __init__(self, weight=1, lookback_days=5):
        super().__init__('跌破前低', weight)
        self.lookback_days = lookback_days  # 回看天数
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        for i in range(self.lookback_days, len(df)):
            # 计算前N日的最低价
            window_highs = df['high'].iloc[i - self.lookback_days:i]
            prev_low = window_highs.min()
            
            # 如果收盘价跌破前N日的最低价
            current_close = df['close'].iloc[i]
            if current_close < prev_low:
                signals.iloc[i] = -1
        
        return signals

class CompositeStrategy:
    """
    组合策略: 综合多个指标生成最终信号
    """
    def __init__(self, strategies=None, buy_threshold=0.5, sell_threshold=0.5):
        self.strategies = strategies or [
            MACDGoldenCross(),
            MACDDeathCross(),
            BOLLSupport(),
            BOLLResistance(),
            VolumeBreakout(),
            RSIOversold(),
            KDJGoldenCross(),
            MA20Support(),
            KLinePatternStrategy()
        ]
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
    
    def generate_signals(self, df):
        """
        综合多个策略生成加权信号
        返回: DataFrame with composite_score, signal
        """
        total_weight = sum(s.weight for s in self.strategies)
        
        buy_score = pd.Series(0.0, index=df.index)
        sell_score = pd.Series(0.0, index=df.index)
        signals_detail = {}
        
        for strategy in self.strategies:
            signals = strategy.generate_signals(df)
            buy_score += signals.clip(lower=0) * strategy.weight
            sell_score += (-signals).clip(lower=0) * strategy.weight
            signals_detail[strategy.name] = signals.tolist()
        
        # 归一化
        buy_score = buy_score / total_weight
        sell_score = sell_score / total_weight
        
        # 生成最终信号
        final_signal = pd.Series(0, index=df.index)
        final_signal[buy_score >= self.buy_threshold] = 1
        final_signal[sell_score >= self.sell_threshold] = -1
        
        return pd.DataFrame({
            'buy_score': buy_score,
            'sell_score': sell_score,
            'signal': final_signal,
            'composite_score': buy_score - sell_score
        }, index=df.index), signals_detail


def generate_trading_signals(df, config=None):
    """
    生成交易信号的主函数（优化版 - 防卖飞）
    
    参数:
        df: 包含OHLCV数据的DataFrame
        config: 策略配置
    
    返回:
        带有信号的DataFrame
    """
    if config is None:
        config = {
            'buy_threshold': 0.08,
            'sell_threshold': 0.20  # 卖出阈值更高，大幅防卖飞
        }
    
    # 买入策略（权重较高，更容易产生买入信号）
    buy_strategies = [
        MACDGoldenCross(weight=1.5),
        BOLLSupport(weight=1.2),
        VolumeBreakout(weight=1.0),
        RSIOversold(weight=1.0),
        KDJGoldenCross(weight=1.0),
        MA20Support(weight=1.2),
        KLinePatternStrategy(weight=0.8),
    ]
    
    # 卖出策略（权重大幅降低，更保守防卖飞）
    sell_strategies = [
        MACDDeathCross(weight=0.6),      # MACD死叉权重降低
        BOLLResistance(weight=0.5),      # 布林带上轨权重降低
        VolumeBreakout(weight=0.3),      # 放量下跌
        RSIOversold(weight=0.3),         # RSI超买
        KDJGoldenCross(weight=0.3),      # KDJ死叉
        KLinePatternStrategy(weight=0.3),  # K线形态
        TrailingStopStrategy(weight=1.0, lookback=30, pullback_pct=0.20),  # 移动止盈（条件严格）
        PriceBelowMA20(weight=0.8),      # 跌破MA20
        ConsecutiveDecline(weight=1.0, days=3, decline_threshold=0.05),  # 连续3天跌幅超过5%
        BreakPreviousLow(weight=1.0, lookback_days=5),  # 跌破前5日最低价
    ]
    
    # 合并策略
    all_strategies = buy_strategies + [s for s in sell_strategies if type(s).__name__ not in [type(b).__name__ for b in buy_strategies]]
    
    # 创建组合策略
    composite = CompositeStrategy(
        strategies=all_strategies,
        buy_threshold=config.get('buy_threshold', 0.08),
        sell_threshold=config.get('sell_threshold', 0.12)
    )
    
    result, detail = composite.generate_signals(df)
    
    # 合并结果
    output = df.copy()
    for col in result.columns:
        output[col] = result[col]
    output['signals_detail'] = [detail] * len(df)
    
    return output
