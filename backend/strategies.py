import pandas as pd
import numpy as np

class TradingStrategy:
    """
    交易策略基类
    """
    def __init__(self, name, weight=1, strategy_type='neutral'):
        """
        Parameters:
            name: 策略名称
            weight: 权重（影响信号强度）
            strategy_type: 策略类型
                - 'trend': 趋势策略
                - 'buy': 买入策略
                - 'sell': 卖出策略
                - 'neutral': 中性策略
        """
        self.name = name
        self.weight = weight
        self.strategy_type = strategy_type
    
    def generate_signals(self, df):
        """
        生成信号，返回 Series: 1=买入, -1=卖出, 0=无信号
        """
        raise NotImplementedError

# ========================================
# 1. 趋势判断策略（基础过滤器）
# ========================================

class TrendDetector(TradingStrategy):
    """
    趋势检测策略
    检测当前市场状态：多头、空头、震荡
    """
    def __init__(self, weight=1):
        super().__init__('趋势检测', weight, strategy_type='trend')
    
    def generate_trend(self, df):
        """
        返回趋势状态 Series
        -1: 空头趋势（卖出倾向）
         0: 震荡趋势（中性）
         1: 多头趋势（买入倾向）
        """
        trend = pd.Series(0, index=df.index)
        
        # 多头条件：MA5 > MA10 > MA20，价格在MA20上方
        bullish = (df['ma5'] > df['ma10']) & \
                  (df['ma10'] > df['ma20']) & \
                  (df['close'] > df['ma20']) & \
                  (df['close'] > df['close'].shift(5))  # 5日上涨
        
        # 空头条件：MA5 < < MA10 < MA20，价格在MA20下方
        bearish = (df['ma5'] < df['ma10']) & \
                  (df['ma10'] < df['ma20']) & \
                  (df['close'] < df['ma20']) & \
                  (df['close'] < df['close'].shift(5))  # 5日下跌
        
        trend[bullish] = 1
        trend[bearish] = -1
        
        return trend

# ========================================
# 2. 买入策略
# ========================================

class MACDGoldenCross(TradingStrategy):
    """
    MACD金叉买入策略
    条件: MACD线上穿信号线，且MACD柱状图由负转正
    """
    def __init__(self, weight=1.5):
        super().__init__('MACD金叉买入', weight, strategy_type='buy')
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        # MACD金叉
        golden_cross = (df['macd'] > df['macd_signal']) & \
                      (df['macd'].shift(1) <= df['macd_signal'].shift(1))
        
        # 柱状图为正或刚转正
        hist_positive = df['macd_hist'] > 0
        
        # MACD在零轴上方（多头中金叉更可靠）
        above_zero = df['macd'] > 0
        
        # 金叉且柱状图转正且在零轴上方
        buy_signal = golden_cross & hist_positive & above_zero
        signals[buy_signal] = 1
        
        return signals

class BOLLSupport(TradingStrategy):
    """
    布林带下轨支撑买入策略
    条件: 价格触及下轨后反弹收阳
    """
    def __init__(self, weight=1.2):
        super().__init__('布林带下轨支撑', weight, strategy_type='buy')
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        # 触及下轨
        touch_lower = df['low'] <= df['boll_lower']
        prev_touch = df['low'].shift(1) <= df['boll_lower'].shift(1)
        
        # 反弹：触及下轨后，收盘价回到下轨上方，且收阳
        close_above_lower = df['close'] > df['boll_lower']
        yang_candle = df['close'] > df['open']
        
        buy_signal = prev_touch & close_above_lower & yang_candle
        signals[buy_signal] = 1
        
        return signals

class MA20Support(TradingStrategy):
    """
    MA20均线支撑买入策略
    条件: 价格回踩MA20后反弹
    """
    def __init__(self, weight=1.2):
        super().__init__('MA20支撑', weight, strategy_type='buy')
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        # 接近MA20（偏差<1%）
        near_ma20 = abs(df['close'] - df['ma20']) / df['ma20'] < 0.01
        
        # 前一日也接近
        prev_near = abs(df['close'].shift(1) - df['ma20'].shift(1)) / df['ma20'].shift(1) < 0.01
        
        # 反弹：从前一日的下方反弹到上方，且收阳
        close_above_prev_close = df['close'] > df['close'].shift(1)
        yang_candle = df['close'] > df['open']
        
        buy_signal = prev_near & close_above_prev_close & yang_candle
        signals[buy_signal] = 1
        
        return signals

class VolumeBreakout(TradingStrategy):
    """
    放量突破买入策略
    条件: 成交量放大，价格突破前高
    """
    def __init__(self, weight=1.0):
        super().__init__('放量突破', weight, strategy_type='buy')
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        # 放量
        high_volume = df['vol_ratio'] >= 2.0
        
        # 价格突破前高
        break_high = df['close'] > df['high'].shift(1)
        
        # 收阳
       
        yang_candle = df['close'] > df['open']
        
        buy_signal = high_volume & break_high & yang_candle
        signals[buy_signal] = 1
        
        return signals

class RSIOversold(TradingStrategy):
    """
    RSI超卖买入策略
    条件: RSI < 30（超卖区）并开始回升
    """
    def __init__(self, weight=1.0):
        super().__init__('RSI超卖', weight, strategy_type='buy')
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        # RSI超卖
        oversold = df['rsi'] < 30
        
        # 前一日超卖
        was_oversold = df['rsi'].shift(1) < 30
        
        # 开始回升
        now_rising = df['rsi'] > df['rsi'].shift(1)
        
        buy_signal = was_oversold & now_rising & oversold
        signals[buy_signal] = 1
        
        return signals

class KDJGoldenCross(TradingStrategy):
    """
    KDJ金叉买入策略
    条件: K线上穿D线，且在超卖区
    """
    def __init__(self, weight=1.0):
        super().__init__('KDJ金叉', weight, strategy_type='buy')
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        # KDJ金叉
        golden_cross = (df['kdj_k'] > df['kdj_d']) & \
                      (df['kdj_k'].shift(1) <= df['kdj_d'].shift(1))
        
        # 在超卖区金叉更可靠
        oversold = df['kdj_k'] < 30
        
        buy_signal = golden_cross & oversold
        signals[buy_signal] = 1
        
        return signals

class BottomReversal(TradingStrategy):
    """
    底部反转买入策略
    条件: 价格创新低后出现阳线，MACD柱状图由负转正，成交量放大
    适用于空头趋势末端的超跌反弹捕捉
    """
    def __init__(self, weight=1.5, lookback=10):
        super().__init__('底部反转', weight, strategy_type='buy')
        self.lookback = lookback
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        if len(df) < self.lookback + 1:
            return signals
        
        for i in range(self.lookback, len(df)):
            # 1. 前N日内创新低（当前最低价接近区间最低价）
            window_low = df['low'].iloc[i - self.lookback:i].min()
            near_bottom = df['low'].iloc[i] <= window_low * 1.01  # 允许1%误差
            
            # 2. 出现阳线（收盘价高于开盘价）
            yang_candle = df['close'].iloc[i] > df['open'].iloc[i]
            
            # 3. MACD柱状图由负转正（或从更负变为更正）
            macd_hist_rising = df['macd_hist'].iloc[i] > df['macd_hist'].iloc[i - 1]
            macd_hist_improving = (df['macd_hist'].iloc[i] > 0) or \
                                  (df['macd_hist'].iloc[i] > df['macd_hist'].iloc[i - 1] * 1.5)
            
            # 4. 成交量放大（量比 >= 1.5）
            volume_expand = df['vol_ratio'].iloc[i] >= 1.5
            
            # 5. RSI从超卖区回升（RSI < 40 且正在上升）
            rsi_recovering = (df['rsi'].iloc[i] < 40) and \
                            (df['rsi'].iloc[i] > df['rsi'].iloc[i - 1])
            
            # 组合条件：创新低 + 阳线 + (MACD改善 或 RSI回升) + 放量
            if near_bottom and yang_candle and (macd_hist_improving or rsi_recovering) and volume_expand:
                signals.iloc[i] = 1
        
        return signals

# ========================================
# 3. 卖出策略
# ========================================

class MACDDeathCross(TradingStrategy):
    """
    MACD死叉卖出策略
    条件: MACD线下穿信号线
    """
    def __init__(self, weight=1.5):
        super().__init__('MACD死叉卖出', weight, strategy_type='sell')
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        # MACD死叉
        death_cross = (df['macd'] < df['macd_signal']) & \
                      (df['macd'].shift(1) >= df['macd_signal'].shift(1))
        
        # 在零轴上方死叉更可靠（高位回落）
        above_zero = df['macd'] > 0
        
        sell_signal = death_cross & above_zero
        signals[sell_signal] = -1
        
        return signals

class BOLLResistance(TradingStrategy):
    """
    布林带上轨压力卖出策略
    条件: 触及上轨后回落收阴
    """
    def __init__(self, weight=1.2):
        super().__init__('布林带上轨压力', weight, strategy_type='sell')
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        # 触及上轨
        touch_upper = df['high'] >= df['boll_upper']
        prev_touch = df['high'].shift(1) >= df['boll_upper'].shift(1)
        
        # 回落：从前一日的上轨回落到下方
        close_below_upper = df['close'] < df['boll_upper']
        
        # 出现大阴线（跌幅超过3%）
        big_yin = (df['close'] - df['open']) / df['open'] < -0.03
        
        sell_signal = prev_touch & close_below_upper & big_yin
        signals[sell_signal] = -1
        
        return signals

class PriceBelowMA20(TradingStrategy):
    """
    价格跌破MA20卖出策略
    条件: 价格从MA20上方跌破到下方
    """
    def __init__(self, weight=1.5):
        super().__init__('跌破MA20', weight, strategy_type='sell')
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        # 前一日上方
        above_ma20 = df['close'].shift(1) >= df['ma20'].shift(1)
        
        # 当日下方
        below_ma20 = df['close'] < df['ma20']
        
        # 跌破且收阴
        yin_candle = df['close'] < df['open']
        
        sell_signal = above_ma20 & below_ma20 & yin_candle
        signals[sell_signal] = -1
        
        return signals

class BreakPreviousLow(TradingStrategy):
    """
    跌破前低卖出策略
    条件: 收盘价跌破前N日的最低价
    """
    def __init__(self, weight=1.0, lookback_days=5):
        super().__init__('跌破前低', weight, strategy_type='sell')
        self.lookback_days = lookback_days
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        for i in range(self.lookback_days, len(df)):
            # 计算前N日的最低价
            window = df['high'].iloc[i - self.lookback_days:i]
            prev_low = window.min()
            
            # 如果收盘价跌破前N日的最低价
            current_close = df['close'].iloc[i]
            if current_close < prev_low:
                signals.iloc[i] = -1
        
        return signals

class ConsecutiveDecline(TradingStrategy):
    """
    连续下跌卖出策略
    条件: 连续N天跌幅超过阈值
    """
    def __init__(self, weight=1.0, days=3, decline_threshold=0.05):
        super().__init__('连续下跌', weight, strategy_type='sell')
        self.days = days
        self.decline_threshold = decline_threshold
    
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

class RSIOverbought(TradingStrategy):
    """
    RSI超买卖出策略
    条件: RSI > 70（超买区）并开始回落
    """
    def __init__(self, weight=1.0):
        super().__init__('RSI超买', weight, strategy_type='sell')
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        # RSI超买
        overbought = df['rsi'] > 70
        
        # 前一日超买
        was_overbought = df['rsi'].shift(1) > 70
        
        # 开始回落
        now_falling = df['rsi'] < df['rsi'].shift(1)
        
        sell_signal = was_overbought & now_falling & overbought
        signals[sell_signal] = -1
        
        return signals

class KDJDeathCross(TradingStrategy):
    """
    KDJ死叉卖出策略
    条件: K线下穿D线，且在超买区
    """
    def __init__(self, weight=1.0):
        super().__init__('KDJ死叉', weight, strategy_type='sell')
    
    def generate_signals(self, df):
        signals = pd.Series(0, index=df.index)
        
        # KDJ死叉
        death_cross = (df['kdj_k'] < df['kdj_d']) & \
                      (df['kdj_k'].shift(1) >= df['kdj_d'].shift(1))
        
        # 在超买区（J > 100）
        overbought = df['kdj_j'] > 100
        
        sell_signal = death_cross & overbought
        signals[sell_signal] = -1
        
        return signals

# ========================================
# 4. 组合策略（综合多策略）
# ========================================

class CompositeStrategy:
    """
    组合策略：综合多个指标生成最终信号
    """
    def __init__(self, strategies=None, buy_threshold=0.08, sell_threshold=0.08):
        self.strategies = strategies or self._default_strategies()
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.trend_detector = TrendDetector()
    
    def _default_strategies(self):
        """
        默认策略配置
        """
        # 买入策略（权重合计：9.4）
        buy_strategies = [
            MACDGoldenCross(weight=1.5),
            BOLLSupport(weight=1.2),
            MA20Support(weight=1.2),
            VolumeBreakout(weight=1.0),
            RSIOversold(weight=1.0),
            KDJGoldenCross(weight=1.0),
            BottomReversal(weight=1.5),  # 底部反转策略，捕捉超跌反弹
        ]
        
        # 卖出策略（权重合计：8.7）
        sell_strategies = [
            MACDDeathCross(weight=1.5),
            BOLLResistance(weight=1.2),
            PriceBelowMA20(weight=1.5),
            BreakPreviousLow(weight=1.0, lookback_days=5),
            ConsecutiveDecline(weight=1.0, days=3, decline_threshold=0.05),
            RSIOverbought(weight=1.0),
            KDJDeathCross(weight=1.0),
        ]
        
        return buy_strategies + sell_strategies
    
    def generate_signals(self, df):
        """
        综合多个策略生成加权信号
        返回: DataFrame with buy_score, sell_score, signal, trend
        """
        # 检测测势
        trend = self.trend_detector.generate_trend(df)
        
        # 计算买入/卖出得分
        buy_score = pd.Series(0.0, index=df.index)
        sell_score = pd.Series(0.0, index=df.index)
        
        # 允许在空头趋势下生效的超跌反弹策略名称
        bearish_allowed_buy_strategies = ['布林带下轨支撑', 'RSI超卖', 'KDJ金叉', '底部反转']
        
        for strategy in self.strategies:
            signals = strategy.generate_signals(df)
            
            # 趋势过滤
            if strategy.strategy_type == 'buy':
                # 买入策略：多头/震荡趋势正常生效
                # 空头趋势：只允许超跌反弹类策略生效
                if strategy.name in bearish_allowed_buy_strategies:
                    # 超跌反弹策略：在所有趋势下都生效（空头趋势下权重打折）
                    trend_weight = trend.map({1: 1.0, 0: 1.0, -1: 0.7})
                    signals = signals * trend_weight
                else:
                    # 其他买入策略：只在多头趋势或震荡中有效
                    signals = signals * (trend >= 0)
            elif strategy.strategy_type == 'sell':
                # 卖出策略：只在空头趋势或震荡中有效
                signals = signals * (trend <= 0)
            
            buy_score += signals.clip(lower=0) * strategy.weight
            sell_score += (-signals).clip(lower=0) * strategy.weight
        
        # 归一化
        buy_score = buy_score / 9.4  # 最大买入权重9.4（含底部反转策略）
        sell_score = sell_score / 8.7  # 最大卖出权重8.7
        
        # 生成最终信号
        final_signal = pd.Series(0, index=df.index)
        final_signal[buy_score >= self.buy_threshold] = 1
        final_signal[sell_score >= self.sell_threshold] = -1
        
        # 过滤逻辑：在下跌趋势中，如果连续出现3个以上卖出信号且中间没有买入，则过滤后续卖出
        # 只应用一次过滤，避免多次循环互相干扰
        consecutive_sell_count = 0
        last_buy_idx = -1
        last_sell_idx = -1
        
        for i in range(len(final_signal)):
            if final_signal.iloc[i] == 1:
                # 买入信号：重置计数，记录位置
                consecutive_sell_count = 0
                last_buy_idx = i
                last_sell_idx = -1
            elif final_signal.iloc[i] == -1:
                consecutive_sell_count += 1
                
                # 如果连续卖出 >= 3 且距离上次买入超过10天，则过滤
                days_since_buy = i - last_buy_idx if last_buy_idx >= 0 else i + 1
                
                # 检查是否有足够的间隔（至少5个交易日）
                days_since_last_sell = i - last_sell_idx if last_sell_idx >= 0 else i + 1
                
                if (consecutive_sell_count >= 3 and days_since_buy > 10) or \
                   (consecutive_sell_count >= 2 and days_since_last_sell < 5):
                    final_signal.iloc[i] = 0
                else:
                    last_sell_idx = i
        
        return pd.DataFrame({
            'buy_score': buy_score,
            'sell_score': sell_score,
            'signal': final_signal,
            'trend': trend,
            'composite_score': buy_score - sell_score
        }, index=df.index)


def generate_trading_signals(df, config=None):
    """
    生成交易信号的主函数（体系化优化版）
    
    Parameters:
        df: 包含OHLCV数据的DataFrame
        config: 策略配置
            - buy_threshold: 买入阈值（默认0.08）
            - sell_threshold: 卖出阈值（默认0.08）
    
    Returns:
        DataFrame with buy_score, sell_score, signal, trend, composite_score
    """
    if config is None:
        config = {
            'buy_threshold': 0.08,
            'sell_threshold': 0.08
        }
    
    composite = CompositeStrategy(
        buy_threshold=config.get('buy_threshold', 0.08),
        sell_threshold=config.get('sell_threshold', 0.08)
    )
    
    return composite.generate_signals(df)
