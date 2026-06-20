import numpy as np
import pandas as pd


def calculate_ema(data, period):
    """计算指数移动平均线"""
    return data.ewm(span=period, adjust=False).mean()


def calculate_sma(data, period):
    """计算简单移动平均线"""
    return data.rolling(window=period).mean()


def calculate_rma(data, period):
    """
    计算 Wilder's Moving Average (RMA)
    用于 RSI 等指标的标准平滑算法
    """
    alpha = 1.0 / period
    return data.ewm(alpha=alpha, adjust=False).mean()


def calculate_macd(df, fast=12, slow=26, signal=9):
    """
    计算MACD指标
    返回: DataFrame with macd, signal, hist
    """
    close = df["close"]
    ema_fast = calculate_ema(close, fast)
    ema_slow = calculate_ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line

    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "hist": histogram}, index=df.index)


def calculate_boll(df, period=20, std_dev=2):
    """
    计算布林带
    返回: DataFrame with upper, middle, lower
    """
    close = df["close"]
    middle = calculate_sma(close, period)
    std = close.rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)

    return pd.DataFrame(
        {"upper": upper, "middle": middle, "lower": lower, "bandwidth": (upper - lower) / middle * 100},  # 带宽百分比
        index=df.index,
    )


def calculate_rsi(df, period=14):
    """
    计算RSI相对强弱指标 (Wilder's RSI)
    使用 Wilder's RMA 进行平滑，符合标准交易平台实现
    返回: Series
    """
    close = df["close"]
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)

    avg_gain = calculate_rma(gain, period)
    avg_loss = calculate_rma(loss, period)

    rs = np.where(avg_loss == 0, 100, avg_gain / avg_loss)
    rsi = 100 - (100 / (1 + rs))

    return pd.Series(rsi, index=df.index)


def calculate_kdj(df, n=9, m1=3, m2=3):
    """
    计算KDJ指标
    返回: DataFrame with k, d, j
    """
    low_min = df["low"].rolling(window=n).min()
    high_max = df["high"].rolling(window=n).max()

    rsv = (df["close"] - low_min) / (high_max - low_min) * 100

    k = pd.Series(np.nan, index=df.index)
    d = pd.Series(np.nan, index=df.index)

    # 数据不足时返回空值
    if len(df) < n:
        j = 3 * k - 2 * d
        return pd.DataFrame({"k": k, "d": d, "j": j}, index=df.index)

    # 初始化
    k.iloc[n - 1] = 50
    d.iloc[n - 1] = 50

    for i in range(n, len(df)):
        k.iloc[i] = (m1 - 1) / m1 * k.iloc[i - 1] + 1 / m1 * rsv.iloc[i]
        d.iloc[i] = (m2 - 1) / m2 * d.iloc[i - 1] + 1 / m2 * k.iloc[i]

    j = 3 * k - 2 * d

    return pd.DataFrame({"k": k, "d": d, "j": j}, index=df.index)


def calculate_ma_cross(df):
    """
    计算均线交叉信号
    返回: 均线数据和交叉信号
    """
    ma5 = calculate_sma(df["close"], 5)
    ma10 = calculate_sma(df["close"], 10)
    ma20 = calculate_sma(df["close"], 20)
    ma60 = calculate_sma(df["close"], 60)

    # 金叉/死叉检测
    ma5_ma10_cross = ma5 > ma10
    golden_cross = ma5_ma10_cross & (~ma5_ma10_cross.shift(1, fill_value=False))
    death_cross = (~ma5_ma10_cross) & ma5_ma10_cross.shift(1, fill_value=False)

    return pd.DataFrame(
        {
            "ma5": ma5,
            "ma10": ma10,
            "ma20": ma20,
            "ma60": ma60,
            "golden_cross": golden_cross,
            "death_cross": death_cross,
        },
        index=df.index,
    )


def calculate_volume_ratio(df, period=5):
    """
    计算量比
    """
    vol_ma = calculate_sma(df["volume"], period)
    vol_ratio = df["volume"] / vol_ma
    return vol_ratio


def detect_kline_pattern(df):
    """
    检测K线形态
    返回: Series with pattern names
    """
    patterns = pd.Series("", index=df.index)

    # 实体和影线计算
    body = abs(df["close"] - df["open"])
    upper_shadow = df["high"] - df[["close", "open"]].max(axis=1)
    lower_shadow = df[["close", "open"]].min(axis=1) - df["low"]
    total_range = df["high"] - df["low"]

    # 十字星: 实体很小，影线较长
    doji = (body / total_range < 0.1) & (total_range > 0)
    patterns[doji] = "十字星"

    # 锤子线: 下影线长，上影线短，实体在上方
    hammer = (lower_shadow > body * 2) & (upper_shadow < body * 0.5) & (total_range > 0)
    patterns[hammer] = "锤子线"

    # 射击之星: 上影线长，下影线短
    shooting_star = (upper_shadow > body * 2) & (lower_shadow < body * 0.5) & (total_range > 0)
    patterns[shooting_star] = "射击之星"

    # 大阳线: 实体大，阳线
    big_yang = (body / total_range > 0.7) & (df["close"] > df["open"])
    patterns[big_yang] = "大阳线"

    # 大阴线: 实体大，阴线
    big_yin = (body / total_range > 0.7) & (df["close"] < df["open"])
    patterns[big_yin] = "大阴线"

    return patterns


def detect_candle_patterns(df):
    """
    检测K线组合形态
    """
    patterns = pd.Series("", index=df.index)

    for i in range(1, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i - 1]

        curr_body = abs(curr["close"] - curr["open"])

        # 看涨吞没
        if (
            prev["close"] < prev["open"]
            and curr["close"] > curr["open"]  # 前一根阴线
            and curr["open"] < prev["close"]  # 当前阳线
            and curr["close"] > prev["open"]  # 开盘低于前收盘
        ):  # 收盘高于前开盘
            patterns.iloc[i] = "看涨吞没"

        # 看跌吞没
        elif (
            prev["close"] > prev["open"]
            and curr["close"] < curr["open"]  # 前一根阳线
            and curr["open"] > prev["close"]  # 当前阴线
            and curr["close"] < prev["open"]  # 开盘高于前收盘
        ):  # 收盘低于前开盘
            patterns.iloc[i] = "看跌吞没"

        # 早晨之星 (简化版)
        elif i >= 2:
            prev2 = df.iloc[i - 2]
            if (
                prev2["close"] < prev2["open"]
                and abs(prev["close"] - prev["open"]) < curr_body * 0.3  # 第一根阴线
                and curr["close"] > curr["open"]  # 中间小实体
                and curr["close"] > (prev2["open"] + prev2["close"]) / 2  # 第三根阳线
            ):  # 收盘超过第一根中点
                patterns.iloc[i] = "早晨之星"

        # 黄昏之星 (简化版)
        elif i >= 2:
            prev2 = df.iloc[i - 2]
            if (
                prev2["close"] > prev2["open"]
                and abs(prev["close"] - prev["open"]) < curr_body * 0.3  # 第一根阳线
                and curr["close"] < curr["open"]  # 中间小实体
                and curr["close"] < (prev2["open"] + prev2["close"]) / 2  # 第三根阴线
            ):  # 收盘低于第一根中点
                patterns.iloc[i] = "黄昏之星"

    return patterns


def _momentum_level(score):
    """根据得分划分动能等级"""
    if score >= 80:
        return "极强"
    if score >= 60:
        return "强势"
    if score >= 40:
        return "中性"
    if score >= 20:
        return "弱势"
    return "极弱"


def _score_price_trend(row):
    """价格趋势得分（满分 25）：基于收盘价相对 MA5/MA10/MA20/MA60 的位置"""
    close = row.get("close")
    ma5 = row.get("ma5")
    ma10 = row.get("ma10")
    ma20 = row.get("ma20")
    ma60 = row.get("ma60")
    if pd.isna(close) or close is None:
        return 0.0

    score = 0.0
    if pd.notna(ma5) and close > ma5:
        score += 5
    if pd.notna(ma10) and close > ma10:
        score += 5
    if pd.notna(ma20) and close > ma20:
        score += 7
    if pd.notna(ma60) and close > ma60:
        score += 3

    if pd.notna(ma5) and pd.notna(ma10) and pd.notna(ma20):
        if ma5 > ma10 > ma20:
            score += 5
    return min(score, 25.0)


def _score_ma_slope(df, idx, period=5):
    """MA20 斜率得分（满分 15）：近 N 日 MA20 涨跌幅"""
    if idx < period or "ma20" not in df.columns:
        return 0.0
    cur_ma = df["ma20"].iloc[idx]
    prev_ma = df["ma20"].iloc[idx - period]
    if pd.isna(cur_ma) or pd.isna(prev_ma) or prev_ma <= 0:
        return 0.0
    slope_pct = (cur_ma - prev_ma) / prev_ma * 100
    if slope_pct >= 1.0:
        return 15.0
    if slope_pct >= 0.5:
        return 12.0
    if slope_pct >= 0:
        return 8.0
    if slope_pct >= -0.5:
        return 4.0
    return 0.0


def _score_price_change(df, idx, period=20):
    """价格涨幅得分（满分 20）：近 N 日累计涨幅"""
    if idx < period:
        return 0.0
    cur_close = df["close"].iloc[idx]
    prev_close = df["close"].iloc[idx - period]
    if pd.isna(cur_close) or pd.isna(prev_close) or prev_close <= 0:
        return 0.0
    change_pct = (cur_close - prev_close) / prev_close * 100
    if change_pct >= 20:
        return 20.0
    if change_pct >= 10:
        return 16.0
    if change_pct >= 5:
        return 12.0
    if change_pct >= 0:
        return 8.0
    if change_pct >= -5:
        return 4.0
    return 0.0


def _score_macd_momentum(df, idx):
    """MACD 动能得分（满分 15）：MACD 柱变化 + DIF/DEA 关系"""
    if idx < 1:
        return 0.0
    cur_hist = df["macd_hist"].iloc[idx]
    prev_hist = df["macd_hist"].iloc[idx - 1]
    cur_macd = df["macd"].iloc[idx]
    cur_signal = df["macd_signal"].iloc[idx]
    if pd.isna(cur_hist) or pd.isna(cur_macd) or pd.isna(cur_signal):
        return 0.0

    score = 0.0
    if cur_hist > 0:
        score += 4
        if pd.notna(prev_hist) and cur_hist > prev_hist:
            score += 4
    else:
        if pd.notna(prev_hist) and cur_hist > prev_hist:
            score += 2

    if cur_macd > cur_signal:
        score += 4
    if cur_macd > 0:
        score += 3
    return min(score, 15.0)


def _score_rsi(row):
    """RSI 强度得分（满分 10）：50-70 为最佳强势区间"""
    rsi = row.get("rsi")
    if pd.isna(rsi) or rsi is None:
        return 0.0
    if 55 <= rsi <= 70:
        return 10.0
    if 50 <= rsi < 55:
        return 8.0
    if 70 < rsi <= 80:
        return 7.0
    if 45 <= rsi < 50:
        return 5.0
    if 80 < rsi <= 90:
        return 4.0
    if 30 <= rsi < 45:
        return 3.0
    return 1.0


def _score_volume(df, idx):
    """成交量动能得分（满分 10）：量比 + 价升量增"""
    if idx < 1:
        return 0.0
    vol_ratio = df["vol_ratio"].iloc[idx] if "vol_ratio" in df.columns else None
    cur_close = df["close"].iloc[idx]
    prev_close = df["close"].iloc[idx - 1]
    cur_vol = df["volume"].iloc[idx]
    prev_vol = df["volume"].iloc[idx - 1]
    if pd.isna(vol_ratio) or vol_ratio is None:
        return 0.0

    score = 0.0
    if vol_ratio >= 2.0:
        score += 5
    elif vol_ratio >= 1.5:
        score += 4
    elif vol_ratio >= 1.0:
        score += 3
    elif vol_ratio >= 0.7:
        score += 2

    if pd.notna(cur_close) and pd.notna(prev_close) and pd.notna(cur_vol) and pd.notna(prev_vol):
        if cur_close > prev_close and cur_vol > prev_vol:
            score += 5
        elif cur_close > prev_close:
            score += 3
    return min(score, 10.0)


def _score_52w_position(df, idx):
    """52周位置得分（满分 5）：当前价相对 52 周高低点位置"""
    lookback = min(idx + 1, 252)
    if lookback < 20:
        return 0.0
    window = df.iloc[idx - lookback + 1 : idx + 1]
    high_52w = window["high"].max()
    low_52w = window["low"].min()
    cur_close = df["close"].iloc[idx]
    if pd.isna(high_52w) or pd.isna(low_52w) or high_52w <= low_52w:
        return 0.0
    position = (cur_close - low_52w) / (high_52w - low_52w)
    if position >= 0.9:
        return 5.0
    if position >= 0.7:
        return 4.0
    if position >= 0.5:
        return 3.0
    if position >= 0.3:
        return 2.0
    return 1.0


def calculate_momentum_score(df):
    """计算个股动能指标（0-100）

    返回 DataFrame: momentum_score, momentum_level, 以及各分项得分列
    """
    scores = []
    levels = []
    trend_scores = []
    slope_scores = []
    change_scores = []
    macd_scores = []
    rsi_scores = []
    vol_scores = []
    pos_scores = []

    for idx in range(len(df)):
        row = df.iloc[idx]
        s_trend = _score_price_trend(row)
        s_slope = _score_ma_slope(df, idx)
        s_change = _score_price_change(df, idx)
        s_macd = _score_macd_momentum(df, idx)
        s_rsi = _score_rsi(row)
        s_vol = _score_volume(df, idx)
        s_pos = _score_52w_position(df, idx)
        total = s_trend + s_slope + s_change + s_macd + s_rsi + s_vol + s_pos
        total = round(max(0.0, min(100.0, total)), 2)
        scores.append(total)
        levels.append(_momentum_level(total))
        trend_scores.append(round(s_trend, 2))
        slope_scores.append(round(s_slope, 2))
        change_scores.append(round(s_change, 2))
        macd_scores.append(round(s_macd, 2))
        rsi_scores.append(round(s_rsi, 2))
        vol_scores.append(round(s_vol, 2))
        pos_scores.append(round(s_pos, 2))

    return pd.DataFrame(
        {
            "momentum_score": scores,
            "momentum_level": levels,
            "mom_trend": trend_scores,
            "mom_slope": slope_scores,
            "mom_change": change_scores,
            "mom_macd": macd_scores,
            "mom_rsi": rsi_scores,
            "mom_volume": vol_scores,
            "mom_position": pos_scores,
        },
        index=df.index,
    )


def calculate_all_indicators(df, rsi_period=14):
    """
    计算所有技术指标
    """
    result = df.copy()

    # MACD
    macd = calculate_macd(df)
    result["macd"] = macd["macd"]
    result["macd_signal"] = macd["signal"]
    result["macd_hist"] = macd["hist"]

    # 布林带
    boll = calculate_boll(df)
    result["boll_upper"] = boll["upper"]
    result["boll_middle"] = boll["middle"]
    result["boll_lower"] = boll["lower"]
    result["boll_width"] = boll["bandwidth"]

    # RSI
    result["rsi"] = calculate_rsi(df, period=rsi_period)

    # KDJ
    kdj = calculate_kdj(df)
    result["kdj_k"] = kdj["k"]
    result["kdj_d"] = kdj["d"]
    result["kdj_j"] = kdj["j"]

    # 均线
    ma = calculate_ma_cross(df)
    result["ma5"] = ma["ma5"]
    result["ma10"] = ma["ma10"]
    result["ma20"] = ma["ma20"]
    result["ma60"] = ma["ma60"]

    # 量比
    result["vol_ratio"] = calculate_volume_ratio(df)

    # K线形态
    result["kline_pattern"] = detect_kline_pattern(df)
    result["candle_pattern"] = detect_candle_patterns(df)

    # 动能指标（需在 MACD/RSI/MA/vol_ratio 计算后）
    momentum = calculate_momentum_score(result)
    for col in momentum.columns:
        result[col] = momentum[col]

    return result


def find_support_resistance(df, lookback_days=60, n_support=3, n_resistance=3):
    """
    计算支撑位和压力位
    算法：历史高低点 + 均线支撑/压力

    返回: {
        'support_levels': [{'price': float, 'type': str, 'strength': str}],
        'resistance_levels': [{'price': float, 'type': str, 'strength': str}]
    }
    """
    if len(df) < 20:
        return {"support_levels": [], "resistance_levels": []}

    # 取最近N天数据
    recent_df = df.tail(lookback_days)
    current_price = df["close"].iloc[-1]

    levels = []

    # 1. 历史高低点 (局部极值)
    # 局部高点检测
    highs = recent_df["high"].values
    for i in range(2, len(highs) - 2):
        if highs[i] > highs[i - 1] and highs[i] > highs[i - 2] and highs[i] > highs[i + 1] and highs[i] > highs[i + 2]:
            levels.append({"price": highs[i], "type": "历史高点", "strength": "强"})

    # 局部低点检测
    lows = recent_df["low"].values
    for i in range(2, len(lows) - 2):
        if lows[i] < lows[i - 1] and lows[i] < lows[i - 2] and lows[i] < lows[i + 1] and lows[i] < lows[i + 2]:
            levels.append({"price": lows[i], "type": "历史低点", "strength": "强"})

    # 2. 均线支撑/压力
    ma_periods = [20, 60]
    for period in ma_periods:
        if len(df) >= period:
            ma_value = calculate_sma(df["close"], period).iloc[-1]
            if not pd.isna(ma_value):
                if ma_value < current_price:
                    levels.append({"price": ma_value, "type": f"MA{period}", "strength": "中"})
                else:
                    levels.append({"price": ma_value, "type": f"MA{period}", "strength": "中"})

    # 3. 布林带上下轨
    boll = calculate_boll(df)
    if not pd.isna(boll["upper"].iloc[-1]):
        levels.append({"price": boll["upper"].iloc[-1], "type": "布林上轨", "strength": "中"})
    if not pd.isna(boll["lower"].iloc[-1]):
        levels.append({"price": boll["lower"].iloc[-1], "type": "布林下轨", "strength": "中"})

    # 分离支撑位（低于当前价）和压力位（高于当前价）
    support_levels = [lvl for lvl in levels if lvl["price"] < current_price]
    resistance_levels = [lvl for lvl in levels if lvl["price"] > current_price]

    # 按距离当前价排序：支撑位从高到低（接近当前价在前），压力位从低到高
    support_levels = sorted(support_levels, key=lambda x: -x["price"])
    resistance_levels = sorted(resistance_levels, key=lambda x: x["price"])

    # 合并相近价位 (间距小于1%视为同一价位)
    def merge_close_levels(levels, threshold=0.01):
        if not levels:
            return []
        merged = [levels[0]]
        for level in levels[1:]:
            last = merged[-1]
            if abs(level["price"] - last["price"]) / last["price"] < threshold:
                # 合并：取平均值，强度升级
                last["price"] = (last["price"] + level["price"]) / 2
                if last["strength"] == "中" and level["strength"] == "强":
                    last["strength"] = "强"
                if last["type"] != level["type"]:
                    last["type"] = last["type"] + "/" + level["type"]
            else:
                merged.append(level)
        return merged

    support_levels = merge_close_levels(support_levels)
    resistance_levels = merge_close_levels(resistance_levels)

    # 只保留指定数量
    support_levels = support_levels[:n_support]
    resistance_levels = resistance_levels[:n_resistance]

    return {"support_levels": support_levels, "resistance_levels": resistance_levels}


def detect_volume_price_patterns(df, config=None):
    """识别量价形态

    识别三种经典量价场景：
    1. 放量突破 + 回踩缩量 → 真突破概率较高
    2. 放量破位 → 止损信号
    3. 高位放量滞涨/下跌 → 危险信号

    Args:
        df: 已计算完所有指标的 DataFrame，需含 vol_ratio, ma20, boll_*, rsi,
            pct_change, turnover, open, close, high, low, volume
        config: 可选的参数覆盖，dict 格式同 pattern_config.PATTERN_CONFIG

    Returns:
        list[dict]: 识别到的形态列表，每项包含 pattern, name, desc, confidence,
                    action, details
    """
    from pattern_config import PATTERN_CONFIG

    merged_config = PATTERN_CONFIG.copy()
    if config:
        for key in merged_config:
            if key in config:
                merged_config[key].update(config[key])

    if df is None or len(df) < 25:
        return []

    if "vol_ratio" not in df.columns:
        return []

    patterns = []
    idx = len(df) - 1
    row = df.iloc[idx]

    vol_ratio = _safe_get(row, "vol_ratio")
    close = _safe_get(row, "close")
    open_ = _safe_get(row, "open")
    pct_change = _safe_get(row, "pct_change")
    turnover = _safe_get(row, "turnover")
    rsi = _safe_get(row, "rsi")
    ma20 = _safe_get(row, "ma20")
    boll_lower = _safe_get(row, "boll_lower")

    if vol_ratio is None or close is None or open_ is None:
        return []

    _check_true_breakout(df, idx, merged_config["true_breakout"], patterns)
    _check_volume_breakdown(
        df, idx, merged_config["volume_breakdown"], patterns,
        vol_ratio, close, open_, pct_change, ma20, boll_lower,
    )
    _check_top_divergence(
        df, idx, merged_config["top_divergence"], patterns,
        vol_ratio, close, open_, pct_change, turnover, rsi,
    )

    return patterns


def _safe_get(row, col, default=None):
    """安全获取 DataFrame 行中的列值"""
    if col in row.index:
        val = row[col]
        return val if pd.notna(val) else default
    return default


def _check_true_breakout(df, idx, cfg, patterns):
    """形态一：放量突破 + 回踩缩量"""
    lookback = cfg["lookback_days"]
    resistance_window = cfg["resistance_window"]
    breakout_vol_threshold = cfg["breakout_vol_ratio"]
    pullback_vol_ratio = cfg["pullback_vol_ratio"]
    pullback_vol_pct = cfg["pullback_vol_pct"]

    if idx < lookback + resistance_window:
        return

    cur_vol_ratio = _safe_get(df.iloc[idx], "vol_ratio")
    if cur_vol_ratio is None:
        return
    cur_volume = df["volume"].iloc[idx]
    cur_close = df["close"].iloc[idx]

    # 回看最近 lookback 天寻找突破日
    breakout_idx = None
    for i in range(idx - 1, max(idx - lookback, resistance_window) - 1, -1):
        row_i = df.iloc[i]
        vr_i = _safe_get(row_i, "vol_ratio")
        if vr_i is None:
            continue
        close_i = row_i["close"]
        open_i = row_i["open"]

        if vr_i < breakout_vol_threshold:
            continue
        if close_i <= open_i:
            continue
        resistance_high = df["high"].iloc[i - resistance_window:i].max()
        if pd.isna(resistance_high) or close_i <= resistance_high:
            continue

        breakout_idx = i
        break

    if breakout_idx is None:
        return

    breakout_row = df.iloc[breakout_idx]
    breakout_close = breakout_row["close"]
    breakout_open = breakout_row["open"]
    breakout_vol = breakout_row["volume"]
    breakout_vr = breakout_row["vol_ratio"]
    breakout_date = df.index[breakout_idx]
    breakout_date_str = breakout_date.strftime("%Y-%m-%d") if hasattr(breakout_date, "strftime") else str(breakout_date)

    # 回踩条件：close < 突破日 close 且 close > 突破日 open
    if not (cur_close < breakout_close and cur_close > breakout_open):
        return

    # 缩量条件
    is_shrink_ratio = cur_vol_ratio < pullback_vol_ratio
    is_shrink_pct = cur_volume < breakout_vol * pullback_vol_pct
    if not (is_shrink_ratio or is_shrink_pct):
        return

    # 量价趋势
    vols_after = df["volume"].iloc[breakout_idx + 1:idx + 1].tolist()
    volume_trend = "decreasing"
    if len(vols_after) >= 2:
        increasing_count = sum(1 for j in range(1, len(vols_after)) if vols_after[j] > vols_after[j - 1])
        if increasing_count > len(vols_after) * 0.5:
            volume_trend = "increasing"
        elif increasing_count > len(vols_after) * 0.3:
            volume_trend = "flat"

    # 置信度
    confidence = 0.6
    if volume_trend == "decreasing":
        confidence += 0.15
    if cur_vol_ratio < 0.6:
        confidence += 0.1
    if breakout_vr >= 2.0:
        confidence += 0.1
    confidence = min(confidence, 0.95)

    patterns.append({
        "pattern": "true_breakout",
        "name": "放量突破+回踩缩量",
        "desc": f"{breakout_date_str}放量突破(量比{breakout_vr:.1f})，当前回踩缩量(量比{cur_vol_ratio:.1f})，真突破概率较高",
        "confidence": round(confidence, 2),
        "action": "持有/逢低加仓",
        "details": {
            "breakout_date": breakout_date_str,
            "breakout_vol_ratio": round(float(breakout_vr), 2),
            "pullback_vol_ratio": round(float(cur_vol_ratio), 2),
            "volume_trend": volume_trend,
        },
    })


def _check_volume_breakdown(df, idx, cfg, patterns, vol_ratio, close, open_, pct_change, ma20, boll_lower):
    """形态二：放量破位"""
    vol_threshold = cfg["vol_ratio"]
    pct_threshold = cfg["pct_change_threshold"]
    support_window = cfg["support_window"]

    if idx < support_window:
        return

    if vol_ratio is None or vol_ratio < vol_threshold:
        return

    if close >= open_:
        return

    if pct_change is None or pct_change > pct_threshold:
        return

    # 破位：跌破前 N 日最低价 或 MA20 或 BOLL 下轨
    support_low = df["low"].iloc[idx - support_window:idx].min()
    broke_support = False
    break_type = ""
    if not pd.isna(support_low) and close < support_low:
        broke_support = True
        break_type = f"跌破{support_window}日支撑({support_low:.2f})"
    elif ma20 is not None and close < ma20:
        broke_support = True
        break_type = f"跌破MA20({ma20:.2f})"
    elif boll_lower is not None and close < boll_lower:
        broke_support = True
        break_type = f"跌破BOLL下轨({boll_lower:.2f})"

    if not broke_support:
        return

    confidence = 0.7 + min(vol_ratio - 1.5, 1.5) / 5.0
    confidence = min(confidence, 0.95)

    patterns.append({
        "pattern": "volume_breakdown",
        "name": "放量破位",
        "desc": f"量比{vol_ratio:.1f}放量下跌，{break_type}，跌幅{pct_change:.1f}%，支撑位买盘被打穿",
        "confidence": round(confidence, 2),
        "action": "止损/离场观望",
        "details": {
            "vol_ratio": round(float(vol_ratio), 2),
            "pct_change": round(float(pct_change), 2),
            "break_type": break_type,
        },
    })


def _check_top_divergence(df, idx, cfg, patterns, vol_ratio, close, open_, pct_change, turnover, rsi):
    """形态三：高位放量滞涨/下跌"""
    vol_threshold = cfg["vol_ratio"]
    high_percentile = cfg["high_percentile"]
    cumulative_return_threshold = cfg["cumulative_return"]
    rsi_overbought = cfg["rsi_overbought"]
    stagnant_range = cfg["stagnant_range"]
    decline_threshold = cfg["decline_threshold"]
    turnover_threshold = cfg["turnover_threshold"]

    if idx < 20:
        return

    if vol_ratio is None or vol_ratio < vol_threshold:
        return

    # 高位判断（三选一）
    close_20d = df["close"].iloc[idx - 20:idx + 1]
    percentile_val = np.percentile(close_20d, high_percentile)
    is_high_percentile = close >= percentile_val

    cum_return = (close / df["close"].iloc[idx - 20] - 1) * 100
    is_high_return = cum_return > cumulative_return_threshold

    is_high_rsi = rsi is not None and rsi > rsi_overbought

    if not (is_high_percentile or is_high_return or is_high_rsi):
        return

    # 高位原因描述
    high_reasons = []
    if is_high_percentile:
        high_reasons.append(f"股价处于20日{high_percentile}%分位")
    if is_high_return:
        high_reasons.append(f"20日累计涨幅{cum_return:.1f}%")
    if is_high_rsi:
        high_reasons.append(f"RSI({rsi:.0f})超买")
    high_desc = "、".join(high_reasons)

    # 滞涨或下跌
    if pct_change is None:
        return

    is_stagnant = abs(pct_change) < stagnant_range and close <= open_
    is_decline = pct_change < decline_threshold and close < open_

    if not is_stagnant and not is_decline:
        return

    # 置信度
    confidence = 0.65
    if is_high_return:
        confidence += 0.1
    if is_high_rsi:
        confidence += 0.1
    if turnover is not None and turnover > turnover_threshold:
        confidence += 0.1
    confidence = min(confidence, 0.95)

    if is_stagnant:
        pattern_id = "top_stagnant"
        pattern_name = "高位放量滞涨"
        desc = f"{high_desc}，量比{vol_ratio:.1f}放量但涨幅仅{pct_change:.1f}%，筹码从强手转弱手"
        action = "减仓/离场"
    else:
        pattern_id = "top_decline"
        pattern_name = "高位放量下跌"
        desc = f"{high_desc}，量比{vol_ratio:.1f}放量下跌{pct_change:.1f}%，主力出货信号"
        action = "减仓/止损"

    details = {
        "vol_ratio": round(float(vol_ratio), 2),
        "pct_change": round(float(pct_change), 2),
        "high_reason": high_desc,
    }
    if turnover is not None:
        details["turnover"] = round(float(turnover), 2)

    patterns.append({
        "pattern": pattern_id,
        "name": pattern_name,
        "desc": desc,
        "confidence": round(confidence, 2),
        "action": action,
        "details": details,
    })
