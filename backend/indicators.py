import numpy as np
import pandas as pd

def calculate_ema(data, period):
    """计算指数移动平均线"""
    return data.ewm(span=period, adjust=False).mean()

def calculate_sma(data, period):
    """计算简单移动平均线"""
    return data.rolling(window=period).mean()

def calculate_macd(df, fast=12, slow=26, signal=9):
    """
    计算MACD指标
    返回: DataFrame with macd, signal, hist
    """
    close = df['close']
    ema_fast = calculate_ema(close, fast)
    ema_slow = calculate_ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    
    return pd.DataFrame({
        'macd': macd_line,
        'signal': signal_line,
        'hist': histogram
    }, index=df.index)

def calculate_boll(df, period=20, std_dev=2):
    """
    计算布林带
    返回: DataFrame with upper, middle, lower
    """
    close = df['close']
    middle = calculate_sma(close, period)
    std = close.rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return pd.DataFrame({
        'upper': upper,
        'middle': middle,
        'lower': lower,
        'bandwidth': (upper - lower) / middle * 100  # 带宽百分比
    }, index=df.index)

def calculate_rsi(df, period=14):
    """
    计算RSI相对强弱指标
    返回: Series
    """
    close = df['close']
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)
    
    avg_gain = calculate_sma(gain, period)
    avg_loss = calculate_sma(loss, period)
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calculate_kdj(df, n=9, m1=3, m2=3):
    """
    计算KDJ指标
    返回: DataFrame with k, d, j
    """
    low_min = df['low'].rolling(window=n).min()
    high_max = df['high'].rolling(window=n).max()
    
    rsv = (df['close'] - low_min) / (high_max - low_min) * 100
    
    k = pd.Series(np.nan, index=df.index)
    d = pd.Series(np.nan, index=df.index)
    
    # 数据不足时返回空值
    if len(df) < n:
        j = 3 * k - 2 * d
        return pd.DataFrame({'k': k, 'd': d, 'j': j}, index=df.index)
    
    # 初始化
    k.iloc[n-1] = 50
    d.iloc[n-1] = 50
    
    for i in range(n, len(df)):
        k.iloc[i] = (m1 - 1) / m1 * k.iloc[i-1] + 1/m1 * rsv.iloc[i]
        d.iloc[i] = (m2 - 1) / m2 * d.iloc[i-1] + 1/m2 * k.iloc[i]
    
    j = 3 * k - 2 * d
    
    return pd.DataFrame({'k': k, 'd': d, 'j': j}, index=df.index)

def calculate_ma_cross(df):
    """
    计算均线交叉信号
    返回: 均线数据和交叉信号
    """
    ma5 = calculate_sma(df['close'], 5)
    ma10 = calculate_sma(df['close'], 10)
    ma20 = calculate_sma(df['close'], 20)
    ma60 = calculate_sma(df['close'], 60)
    
    # 金叉/死叉检测
    ma5_ma10_cross = ma5 > ma10
    golden_cross = ma5_ma10_cross & (~ma5_ma10_cross.shift(1).fillna(False))  # 金叉
    death_cross = (~ma5_ma10_cross) & ma5_ma10_cross.shift(1).fillna(False)  # 死叉
    
    return pd.DataFrame({
        'ma5': ma5,
        'ma10': ma10,
        'ma20': ma20,
        'ma60': ma60,
        'golden_cross': golden_cross,
        'death_cross': death_cross
    }, index=df.index)

def calculate_volume_ratio(df, period=5):
    """
    计算量比
    """
    vol_ma = calculate_sma(df['volume'], period)
    vol_ratio = df['volume'] / vol_ma
    return vol_ratio

def detect_kline_pattern(df):
    """
    检测K线形态
    返回: Series with pattern names
    """
    patterns = pd.Series('', index=df.index)
    
    # 实体和影线计算
    body = abs(df['close'] - df['open'])
    upper_shadow = df['high'] - df[['close', 'open']].max(axis=1)
    lower_shadow = df[['close', 'open']].min(axis=1) - df['low']
    total_range = df['high'] - df['low']
    
    # 十字星: 实体很小，影线较长
    doji = (body / total_range < 0.1) & (total_range > 0)
    patterns[doji] = '十字星'
    
    # 锤子线: 下影线长，上影线短，实体在上方
    hammer = (lower_shadow > body * 2) & (upper_shadow < body * 0.5) & (total_range > 0)
    patterns[hammer] = '锤子线'
    
    # 射击之星: 上影线长，下影线短
    shooting_star = (upper_shadow > body * 2) & (lower_shadow < body * 0.5) & (total_range > 0)
    patterns[shooting_star] = '射击之星'
    
    # 大阳线: 实体大，阳线
    big_yang = (body / total_range > 0.7) & (df['close'] > df['open'])
    patterns[big_yang] = '大阳线'
    
    # 大阴线: 实体大，阴线
    big_yin = (body / total_range > 0.7) & (df['close'] < df['open'])
    patterns[big_yin] = '大阴线'
    
    return patterns

def detect_candle_patterns(df):
    """
    检测K线组合形态
    """
    patterns = pd.Series('', index=df.index)
    
    for i in range(1, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        
        curr_body = abs(curr['close'] - curr['open'])
        prev_body = abs(prev['close'] - prev['open'])
        
        # 看涨吞没
        if (prev['close'] < prev['open'] and  # 前一根阴线
            curr['close'] > curr['open'] and  # 当前阳线
            curr['open'] < prev['close'] and  # 开盘低于前收盘
            curr['close'] > prev['open']):    # 收盘高于前开盘
            patterns.iloc[i] = '看涨吞没'
        
        # 看跌吞没
        elif (prev['close'] > prev['open'] and  # 前一根阳线
              curr['close'] < curr['open'] and  # 当前阴线
              curr['open'] > prev['close'] and  # 开盘高于前收盘
              curr['close'] < prev['open']):    # 收盘低于前开盘
            patterns.iloc[i] = '看跌吞没'
        
        # 早晨之星 (简化版)
        elif (i >= 2):
            prev2 = df.iloc[i-2]
            if (prev2['close'] < prev2['open'] and  # 第一根阴线
                abs(prev['close'] - prev['open']) < curr_body * 0.3 and  # 中间小实体
                curr['close'] > curr['open'] and  # 第三根阳线
                curr['close'] > (prev2['open'] + prev2['close']) / 2):  # 收盘超过第一根中点
                patterns.iloc[i] = '早晨之星'
        
        # 黄昏之星 (简化版)
        elif (i >= 2):
            prev2 = df.iloc[i-2]
            if (prev2['close'] > prev2['open'] and  # 第一根阳线
                abs(prev['close'] - prev['open']) < curr_body * 0.3 and  # 中间小实体
                curr['close'] < curr['open'] and  # 第三根阴线
                curr['close'] < (prev2['open'] + prev2['close']) / 2):  # 收盘低于第一根中点
                patterns.iloc[i] = '黄昏之星'
    
    return patterns

def calculate_all_indicators(df):
    """
    计算所有技术指标
    """
    result = df.copy()
    
    # MACD
    macd = calculate_macd(df)
    result['macd'] = macd['macd']
    result['macd_signal'] = macd['signal']
    result['macd_hist'] = macd['hist']
    
    # 布林带
    boll = calculate_boll(df)
    result['boll_upper'] = boll['upper']
    result['boll_middle'] = boll['middle']
    result['boll_lower'] = boll['lower']
    result['boll_width'] = boll['bandwidth']
    
    # RSI
    result['rsi'] = calculate_rsi(df)
    
    # KDJ
    kdj = calculate_kdj(df)
    result['kdj_k'] = kdj['k']
    result['kdj_d'] = kdj['d']
    result['kdj_j'] = kdj['j']
    
    # 均线
    ma = calculate_ma_cross(df)
    result['ma5'] = ma['ma5']
    result['ma10'] = ma['ma10']
    result['ma20'] = ma['ma20']
    result['ma60'] = ma['ma60']
    
    # 量比
    result['vol_ratio'] = calculate_volume_ratio(df)
    
    # K线形态
    result['kline_pattern'] = detect_kline_pattern(df)
    result['candle_pattern'] = detect_candle_patterns(df)
    
    return result
