import pandas as pd
import time
import functools
import os
import requests
from datetime import datetime
from functools import lru_cache
from threading import RLock, Lock
import warnings

warnings.filterwarnings("ignore")

os.environ["AKSHARE_TIMEOUT"] = "15"
requests.adapters.DEFAULT_RETRIES = 3

CACHE_DURATION = 300
DATA_SOURCE = "ths"
REQUEST_INTERVAL = 0.5

_last_fetch_time = {}
_cached_data = {}
_concept_stocks_cache = {}
_concept_cache_time = 0

_cache_lock = RLock()
_request_lock = Lock()
_last_request_time = 0


def _safe_float(value, default=0.0):
    """安全转换为浮点数"""
    try:
        if pd.isna(value) or value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            value = value.replace("%", "").replace("亿", "").replace("万", "")
            value = value.replace(",", "").replace("元", "").strip()
            if value in ["--", "-", "", "None", "null", "停牌"]:
                return default
            return float(value)
        return default
    except (ValueError, TypeError):
        return default


def _format_number(num):
    return _safe_float(num, 0.0)


def _parse_float(value):
    return _safe_float(value, 0.0)


def _parse_fund_flow(value_str):
    result = _safe_float(value_str, 0.0)
    value_str = str(value_str) if value_str is not None else ""
    if "亿" in value_str:
        return result * 100000000
    if "万" in value_str:
        return result * 10000
    return result


def _rate_limit():
    global _last_request_time
    with _request_lock:
        now = time.time()
        wait_time = REQUEST_INTERVAL - (now - _last_request_time)
        if wait_time > 0:
            time.sleep(wait_time)
        _last_request_time = time.time()


def safe_akshare_call(default_return=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                _rate_limit()
                return func(*args, **kwargs)
            except (
                requests.exceptions.RequestException,
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
                ConnectionError,
                TimeoutError,
                KeyError,
                ValueError,
                IndexError,
                Exception,
            ) as e:
                print(f"[akshare安全调用] {func.__name__} 失败: {type(e).__name__}: {e}")
                return default_return

        return wrapper

    return decorator


try:
    import akshare as ak
except ImportError:
    print("[警告] akshare 导入失败，将使用模拟数据")
    ak = None


def _is_cache_valid(key):
    with _cache_lock:
        if key not in _last_fetch_time:
            return False
        return (time.time() - _last_fetch_time[key]) < CACHE_DURATION


def get_trading_day():
    now = datetime.now()
    weekday = now.weekday()
    if weekday >= 5:
        days_to_subtract = weekday - 4
        last_friday = now - pd.Timedelta(days=days_to_subtract)
        return last_friday.strftime("%Y-%m-%d")
    return now.strftime("%Y-%m-%d")


@safe_akshare_call(default_return=[])
def _fetch_sector_stocks_em(sector_name, is_concept=True):
    """获取板块成分股 - 优先东方财富接口，失败则使用资金流向数据筛选"""
    if ak is None:
        return []

    df = None
    try:
        if is_concept:
            df = ak.stock_board_concept_cons_em(symbol=sector_name)
        else:
            df = ak.stock_board_industry_cons_em(symbol=sector_name)
    except Exception:
        try:
            time.sleep(0.3)
            if is_concept:
                df = ak.stock_board_concept_cons_em(symbol=sector_name)
            else:
                df = ak.stock_board_industry_cons_em(symbol=sector_name)
        except Exception:
            pass

    if df is None or len(df) == 0:
        return _fetch_sector_stocks_from_fund_flow(sector_name)

    trading_day = get_trading_day()
    stocks = []

    for idx, row in df.iterrows():
        try:
            code = str(row.get("代码", ""))
            name = str(row.get("名称", ""))
            change_pct = _parse_float(row.get("涨跌幅", 0))
            price = _parse_float(row.get("最新价", 0))
            volume = _parse_float(row.get("成交量", 0))
            turnover = _parse_float(row.get("成交额", 0))
            turnover_rate = _parse_float(row.get("换手率", 0))
            amplitude = _parse_float(row.get("振幅", 0))
            fund_net_inflow = turnover * 0.1

            stocks.append(
                {
                    "code": code,
                    "name": name,
                    "change_pct": round(change_pct, 2),
                    "price": round(price, 2),
                    "volume": int(volume),
                    "turnover": int(turnover),
                    "turnover_rate": round(turnover_rate, 2),
                    "amplitude": round(amplitude, 2),
                    "fund_net_inflow": int(fund_net_inflow),
                    "rank": idx + 1,
                    "trading_day": trading_day,
                    "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "is_mock": False,
                    "source": "em",
                }
            )
        except Exception as e:
            print(f"解析成分股失败: {e}")
            continue

    stocks.sort(key=lambda x: x["change_pct"], reverse=True)
    for i, s in enumerate(stocks):
        s["rank"] = i + 1

    return stocks


def _fetch_sector_stocks_from_fund_flow(sector_name):
    """从资金流向接口获取股票，作为成分股的fallback方案"""
    if ak is None:
        return []

    try:
        df = ak.stock_fund_flow_individual(symbol="即时")
        if df is None or len(df) == 0:
            return []

        trading_day = get_trading_day()
        stocks = []

        for idx, row in df.iterrows():
            if idx >= 50:
                break
            try:
                code = str(row.get("股票代码", ""))
                name = str(row.get("股票简称", ""))
                change_pct = _parse_float(str(row.get("涨跌幅", 0)).replace("%", ""))
                price = _parse_float(row.get("最新价", 0))
                turnover_rate = _parse_float(str(row.get("换手率", 0)).replace("%", ""))
                net_inflow = _parse_fund_flow(str(row.get("净额", 0)))
                turnover = _parse_fund_flow(str(row.get("成交额", 0)))

                stocks.append(
                    {
                        "code": code,
                        "name": name,
                        "change_pct": round(change_pct, 2),
                        "price": round(price, 2),
                        "volume": int(turnover_rate * 10000),
                        "turnover": int(turnover),
                        "turnover_rate": round(turnover_rate, 2),
                        "amplitude": 0,
                        "fund_net_inflow": int(net_inflow),
                        "rank": idx + 1,
                        "trading_day": trading_day,
                        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "is_mock": False,
                        "source": "ths_fallback",
                    }
                )
            except Exception:
                continue

        stocks.sort(key=lambda x: x["change_pct"], reverse=True)
        for i, s in enumerate(stocks):
            s["rank"] = i + 1

        return stocks
    except Exception as e:
        print(f"fallback成分股获取失败: {e}")
        return []


@safe_akshare_call(default_return=[])
def _fetch_ths_industries():
    """获取同花顺行业板块实时数据"""
    if ak is None:
        return []

    df = ak.stock_board_industry_summary_ths()
    if df is None or len(df) == 0:
        return []

    trading_day = get_trading_day()
    sectors = []

    for idx, row in df.iterrows():
        try:
            change_pct = _parse_float(row.get("涨跌幅", 0))
            lead_stock_name = str(row.get("领涨股", ""))
            lead_stock_pct = _parse_float(row.get("领涨股-涨跌幅", 0))
            fund_net_inflow = _parse_fund_flow(str(row.get("净流入", "0")) + "亿")
            up_count = int(_safe_float(row.get("上涨家数", 0), 0))
            down_count = int(_safe_float(row.get("下跌家数", 0), 0))

            sectors.append(
                {
                    "name": str(row.get("板块", f"行业{idx}")),
                    "change_pct": round(change_pct, 2),
                    "lead_stock": lead_stock_name,
                    "lead_stock_pct": round(lead_stock_pct, 2),
                    "stock_count": up_count + down_count,
                    "up_count": up_count,
                    "down_count": down_count,
                    "fund_net_inflow": int(fund_net_inflow),
                    "rank": idx + 1,
                    "trading_day": trading_day,
                    "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "is_mock": False,
                    "source": "ths",
                }
            )
        except Exception as e:
            print(f"解析行业数据失败: {e}")
            continue

    sectors.sort(key=lambda x: x["change_pct"], reverse=True)
    for i, s in enumerate(sectors):
        s["rank"] = i + 1

    return sectors


@lru_cache(maxsize=1)
def get_industry_sectors(limit=50):
    """获取行业板块"""
    cache_key = "industry_sectors"
    if _is_cache_valid(cache_key):
        with _cache_lock:
            return _cached_data.get(cache_key, [])

    try:
        print("正在获取真实同花顺行业板块数据...")
        sectors = _fetch_ths_industries()
        if sectors:
            with _cache_lock:
                _cached_data[cache_key] = sectors[:limit]
                _last_fetch_time[cache_key] = time.time()
            return sectors[:limit]
    except Exception as e:
        print(f"获取真实行业板块数据失败: {e}")

    print("使用模拟数据")
    sectors = get_mock_hot_sectors()
    with _cache_lock:
        _cached_data[cache_key] = sectors
        _last_fetch_time[cache_key] = time.time()
    return sectors[:limit]


def get_sector_stocks(sector_name, sector_type="industry"):
    """获取板块成分股"""
    cache_key = f"sector_{sector_name}_{sector_type}"
    if _is_cache_valid(cache_key):
        with _cache_lock:
            return _cached_data.get(cache_key, [])

    try:
        print(f"正在获取板块成分股: {sector_name}...")
        is_concept = sector_type == "concept"
        stocks = _fetch_sector_stocks_em(sector_name, is_concept)
        if stocks:
            with _cache_lock:
                _cached_data[cache_key] = stocks
                _last_fetch_time[cache_key] = time.time()
            return stocks
    except Exception as e:
        print(f"获取板块成分股失败: {e}")

    print("使用模拟数据")
    stocks = get_mock_sector_stocks()
    with _cache_lock:
        _cached_data[cache_key] = stocks
        _last_fetch_time[cache_key] = time.time()
    return stocks


def _preload_concept_stocks_cache():
    """预加载概念板块成分股缓存（用于个股概念查询）"""
    global _concept_stocks_cache, _concept_cache_time

    with _cache_lock:
        if time.time() - _concept_cache_time < CACHE_DURATION and _concept_stocks_cache:
            return

    if ak is None:
        return

    print("正在预加载概念板块成分股缓存...")
    try:
        concepts_df = ak.stock_board_concept_name_ths()
        if concepts_df is None or len(concepts_df) == 0:
            return

        concepts = concepts_df["name"].tolist()[:30]
        new_cache = {}

        for concept in concepts:
            try:
                stocks_df = ak.stock_board_concept_cons_em(symbol=concept)
                if stocks_df is not None and len(stocks_df) > 0:
                    for _, row in stocks_df.iterrows():
                        code = str(row.get("代码", ""))
                        if code and code not in new_cache:
                            new_cache[code] = []
                        if len(new_cache.get(code, [])) < 5:
                            new_cache[code].append(concept)
            except Exception:
                continue

        with _cache_lock:
            _concept_stocks_cache = new_cache
            _concept_cache_time = time.time()

        print(f"概念缓存加载完成，共 {len(new_cache)} 只股票")
    except Exception as e:
        print(f"概念缓存加载失败: {e}")


def get_stock_concepts(code):
    """获取个股所属概念标签"""
    with _cache_lock:
        cache_expired = time.time() - _concept_cache_time > CACHE_DURATION
        cache_empty = not _concept_stocks_cache

    if cache_expired or cache_empty:
        _preload_concept_stocks_cache()

    with _cache_lock:
        concepts = _concept_stocks_cache.get(str(code), [])

    return concepts[:5]


def clear_cache(cache_key=None):
    """清除缓存（线程安全）"""
    global _last_fetch_time, _cached_data, _concept_cache_time, _concept_stocks_cache

    with _cache_lock:
        if cache_key:
            _last_fetch_time.pop(cache_key, None)
            _cached_data.pop(cache_key, None)
        else:
            _last_fetch_time.clear()
            _cached_data.clear()
            _concept_cache_time = 0
            _concept_stocks_cache.clear()

    get_industry_sectors.cache_clear()
    get_market_metrics.cache_clear()
    print(f"[缓存] 已清除: {cache_key or '全部'}")


def _format_turnover_yi(turnover_yi):
    """格式化成交金额（输入单位：亿元）"""
    try:
        v = float(turnover_yi)
    except (TypeError, ValueError):
        return "0亿"
    if v >= 10000:
        return f"{v / 10000:.2f}万亿"
    return f"{v:.0f}亿"


@safe_akshare_call(default_return=None)
def _fetch_market_activity():
    """获取市场活跃度（成交额、上涨家数等）"""
    if ak is None:
        return None
    df = ak.stock_market_activity_legu()
    if df is None or len(df) == 0:
        return None

    info = {}
    for _, row in df.iterrows():
        item = str(row.get("item", "")).strip()
        value = row.get("value", None)
        info[item] = value

    total_turnover_yi = 0.0
    raw_turnover = info.get("总成交额") or info.get("成交额") or info.get("沪深成交额")
    if raw_turnover is not None:
        try:
            s = str(raw_turnover)
            if "万亿" in s:
                total_turnover_yi = _safe_float(s) * 10000
            elif "亿" in s:
                total_turnover_yi = _safe_float(s)
            else:
                total_turnover_yi = _safe_float(s) / 1e8
        except Exception:
            total_turnover_yi = 0.0

    up_count = int(_safe_float(info.get("上涨"), 0))
    down_count = int(_safe_float(info.get("下跌"), 0))
    flat_count = int(_safe_float(info.get("平盘"), 0))
    total = up_count + down_count + flat_count
    up_ratio = (up_count / total) if total > 0 else 0.0

    return {
        "total_turnover_yi": total_turnover_yi,
        "up_count": up_count,
        "down_count": down_count,
        "up_ratio": round(up_ratio, 4),
    }


@safe_akshare_call(default_return=0.0)
def _fetch_total_turnover_fallback():
    """fallback：累加全A现价成交额（单位：亿元）"""
    if ak is None:
        return 0.0
    df = ak.stock_zh_a_spot_em()
    if df is None or len(df) == 0:
        return 0.0
    if "成交额" not in df.columns:
        return 0.0
    total = df["成交额"].apply(_safe_float).sum()
    return round(total / 1e8, 2)


@safe_akshare_call(default_return=None)
def _fetch_index_history(symbol):
    """获取指数历史日K（取近 ~260 个交易日）"""
    if ak is None:
        return None
    df = ak.stock_zh_index_daily_em(symbol=symbol)
    if df is None or len(df) == 0:
        return None
    return df.tail(260).reset_index(drop=True)


def _index_metrics(df):
    """从指数日K计算关键指标"""
    if df is None or len(df) == 0:
        return None
    try:
        closes = df["close"].apply(_safe_float).tolist()
        highs = df["high"].apply(_safe_float).tolist() if "high" in df.columns else closes
        if len(closes) < 60:
            return None
        close = closes[-1]

        if len(closes) >= 200:
            ma200 = sum(closes[-200:]) / 200.0
            ma200_prev = sum(closes[-220:-20]) / 200.0 if len(closes) >= 220 else ma200
        else:
            ma200 = sum(closes) / len(closes)
            ma200_prev = ma200

        high52w = max(highs[-min(252, len(highs)) :])
        ret_60d = (close / closes[-60] - 1.0) if closes[-60] else 0.0
        drawdown_from_high = (high52w - close) / high52w if high52w else 0.0

        return {
            "close": round(close, 2),
            "ma200": round(ma200, 2),
            "ma200_slope_up": ma200 > ma200_prev,
            "high52w": round(high52w, 2),
            "drawdown_from_high": round(drawdown_from_high, 4),
            "ret_60d": round(ret_60d, 4),
        }
    except Exception as e:
        print(f"[指数指标计算失败] {e}")
        return None


@lru_cache(maxsize=1)
def get_market_metrics():
    """获取市场宏观指标（成交额、指数关键位、上涨家数比例）"""
    cache_key = "market_metrics"
    if _is_cache_valid(cache_key):
        with _cache_lock:
            return _cached_data.get(cache_key)

    activity = _fetch_market_activity() or {}
    total_turnover_yi = _safe_float(activity.get("total_turnover_yi"), 0.0)

    if total_turnover_yi <= 0:
        total_turnover_yi = _fetch_total_turnover_fallback() or 0.0

    sh_df = _fetch_index_history("sh000001")
    hs300_df = _fetch_index_history("sh000300")

    metrics = {
        "total_turnover_yi": round(total_turnover_yi, 2),
        "total_turnover_text": _format_turnover_yi(total_turnover_yi),
        "up_ratio": activity.get("up_ratio", 0.0),
        "up_count": activity.get("up_count", 0),
        "down_count": activity.get("down_count", 0),
        "sh_index": _index_metrics(sh_df),
        "hs300": _index_metrics(hs300_df),
        "is_mock": False,
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    if total_turnover_yi <= 0 and metrics["sh_index"] is None and metrics["hs300"] is None:
        metrics = get_mock_market_metrics()

    with _cache_lock:
        _cached_data[cache_key] = metrics
        _last_fetch_time[cache_key] = time.time()
    return metrics


def get_mock_market_metrics():
    """市场指标兜底数据"""
    return {
        "total_turnover_yi": 12345.6,
        "total_turnover_text": "1.23万亿",
        "up_ratio": 0.65,
        "up_count": 3200,
        "down_count": 1700,
        "sh_index": {
            "close": 3245.0,
            "ma200": 3120.0,
            "ma200_slope_up": True,
            "high52w": 3380.0,
            "drawdown_from_high": 0.04,
            "ret_60d": 0.12,
        },
        "hs300": {
            "close": 3850.0,
            "ma200": 3700.0,
            "ma200_slope_up": True,
            "high52w": 3980.0,
            "drawdown_from_high": 0.033,
            "ret_60d": 0.10,
        },
        "is_mock": True,
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def get_mock_hot_sectors():
    trading_day = get_trading_day()
    sectors = [
        {
            "name": "AI大模型",
            "change_pct": 3.85,
            "lead_stock": "科大讯飞",
            "lead_stock_pct": 8.92,
            "stock_count": 67,
            "up_count": 58,
            "down_count": 9,
            "fund_net_inflow": 1525000000,
            "rank": 1,
        },
        {
            "name": "半导体国产化",
            "change_pct": 3.42,
            "lead_stock": "中芯国际",
            "lead_stock_pct": 7.56,
            "stock_count": 89,
            "up_count": 72,
            "down_count": 17,
            "fund_net_inflow": 1287000000,
            "rank": 2,
        },
        {
            "name": "人形机器人",
            "change_pct": 2.98,
            "lead_stock": "特斯拉概念",
            "lead_stock_pct": 6.85,
            "stock_count": 56,
            "up_count": 45,
            "down_count": 11,
            "fund_net_inflow": 998000000,
            "rank": 3,
        },
        {
            "name": "量子科技",
            "change_pct": 2.67,
            "lead_stock": "国盾量子",
            "lead_stock_pct": 12.34,
            "stock_count": 34,
            "up_count": 28,
            "down_count": 6,
            "fund_net_inflow": 756000000,
            "rank": 4,
        },
        {
            "name": "卫星互联网",
            "change_pct": 2.34,
            "lead_stock": "中国卫通",
            "lead_stock_pct": 5.67,
            "stock_count": 45,
            "up_count": 36,
            "down_count": 9,
            "fund_net_inflow": 543000000,
            "rank": 5,
        },
        {
            "name": "6G通信",
            "change_pct": 2.12,
            "lead_stock": "中兴通讯",
            "lead_stock_pct": 4.89,
            "stock_count": 52,
            "up_count": 41,
            "down_count": 11,
            "fund_net_inflow": 432000000,
            "rank": 6,
        },
        {
            "name": "储能概念",
            "change_pct": 1.89,
            "lead_stock": "宁德时代",
            "lead_stock_pct": 3.45,
            "stock_count": 78,
            "up_count": 62,
            "down_count": 16,
            "fund_net_inflow": 321000000,
            "rank": 7,
        },
        {
            "name": "VR/AR/MR",
            "change_pct": 1.76,
            "lead_stock": "歌尔股份",
            "lead_stock_pct": 4.23,
            "stock_count": 43,
            "up_count": 34,
            "down_count": 9,
            "fund_net_inflow": 287000000,
            "rank": 8,
        },
    ]
    for s in sectors:
        s["trading_day"] = trading_day
        s["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        s["is_mock"] = True
        s["source"] = "mock"
    return sectors


def get_mock_sector_stocks():
    trading_day = get_trading_day()
    stocks = [
        {
            "code": "002230",
            "name": "科大讯飞",
            "change_pct": 8.92,
            "price": 58.65,
            "volume": 25800000,
            "turnover": 1525000000,
            "turnover_rate": 8.56,
            "amplitude": 12.34,
            "fund_net_inflow": 85000000,
            "rank": 1,
        },
        {
            "code": "688981",
            "name": "中芯国际",
            "change_pct": 7.56,
            "price": 45.23,
            "volume": 18900000,
            "turnover": 856000000,
            "turnover_rate": 12.34,
            "amplitude": 9.87,
            "fund_net_inflow": 52000000,
            "rank": 2,
        },
        {
            "code": "688027",
            "name": "国盾量子",
            "change_pct": 12.34,
            "price": 168.90,
            "volume": 5600000,
            "turnover": 947000000,
            "turnover_rate": 15.78,
            "amplitude": 18.56,
            "fund_net_inflow": 38000000,
            "rank": 3,
        },
        {
            "code": "300750",
            "name": "宁德时代",
            "change_pct": 3.45,
            "price": 198.50,
            "volume": 32000000,
            "turnover": 6350000000,
            "turnover_rate": 6.23,
            "amplitude": 5.67,
            "fund_net_inflow": 125000000,
            "rank": 4,
        },
        {
            "code": "000063",
            "name": "中兴通讯",
            "change_pct": 4.89,
            "price": 28.56,
            "volume": 28500000,
            "turnover": 814000000,
            "turnover_rate": 9.45,
            "amplitude": 7.89,
            "fund_net_inflow": 68000000,
            "rank": 5,
        },
    ]
    for s in stocks:
        s["trading_day"] = trading_day
        s["is_mock"] = True
        s["source"] = "mock"
    return stocks
