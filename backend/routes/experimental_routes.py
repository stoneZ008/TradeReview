from flask import request, jsonify, g
import pandas as pd
import requests

from routes import experimental_bp
from auth import (
    requires_roles,
    requires_permission,
    requires_us_market,
    check_backtest_quota,
    increment_backtest_usage,
    add_audit_log,
)
from data_fetcher import fetch_stock_data, get_stock_info
from indicators import calculate_all_indicators, find_support_resistance
from strategies import generate_trading_signals
from strategies_experimental import generate_trading_signals_v2
from backtest import run_backtest
from backtest_experimental import run_backtest_v2


def _signals_to_records(df, signals_df):
    result_df = df.copy()
    for col in ["buy_score", "sell_score", "signal"]:
        result_df[col] = signals_df[col]
    records = []
    for date, row in result_df.iterrows():
        records.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "open": round(row["open"], 2),
                "high": round(row["high"], 2),
                "low": round(row["low"], 2),
                "close": round(row["close"], 2),
                "volume": int(row["volume"]),
                "ma5": round(row["ma5"], 2) if pd.notna(row["ma5"]) else None,
                "ma10": round(row["ma10"], 2) if pd.notna(row["ma10"]) else None,
                "ma20": round(row["ma20"], 2) if pd.notna(row["ma20"]) else None,
                "ma60": round(row["ma60"], 2) if pd.notna(row["ma60"]) else None,
                "boll_upper": round(row["boll_upper"], 2) if pd.notna(row["boll_upper"]) else None,
                "boll_middle": round(row["boll_middle"], 2) if pd.notna(row["boll_middle"]) else None,
                "boll_lower": round(row["boll_lower"], 2) if pd.notna(row["boll_lower"]) else None,
                "macd": round(row["macd"], 4) if pd.notna(row["macd"]) else None,
                "macd_signal": round(row["macd_signal"], 4) if pd.notna(row["macd_signal"]) else None,
                "macd_hist": round(row["macd_hist"], 4) if pd.notna(row["macd_hist"]) else None,
                "rsi": round(row["rsi"], 2) if pd.notna(row["rsi"]) else None,
                "kdj_k": round(row["kdj_k"], 2) if pd.notna(row["kdj_k"]) else None,
                "kdj_d": round(row["kdj_d"], 2) if pd.notna(row["kdj_d"]) else None,
                "kdj_j": round(row["kdj_j"], 2) if pd.notna(row["kdj_j"]) else None,
                "vol_ratio": round(row["vol_ratio"], 2) if pd.notna(row["vol_ratio"]) else None,
                "buy_score": round(row["buy_score"], 3),
                "sell_score": round(row["sell_score"], 3),
                "signal": int(row["signal"]),
                "kline_pattern": row.get("kline_pattern", ""),
                "candle_pattern": row.get("candle_pattern", ""),
            }
        )
    return records


def _format_backtest_result(result):
    trades = []
    for t in result["trades"]:
        trade = {k: v for k, v in t.items()}
        if "date" in trade:
            trade["date"] = (
                trade["date"].strftime("%Y-%m-%d") if hasattr(trade["date"], "strftime") else str(trade["date"])
            )
        trades.append(trade)
    signals = []
    for date, row in result["signals"].iterrows():
        signals.append(
            {
                "date": date.strftime("%Y-%m-%d") if hasattr(date, "strftime") else str(date),
                "close": round(row["close"], 2),
                "signal": int(row["signal"]),
                "buy_score": round(row["buy_score"], 3),
                "sell_score": round(row["sell_score"], 3),
                "ma5": round(row["ma5"], 2) if pd.notna(row.get("ma5", 0)) else 0,
            }
        )
    return {"metrics": result["metrics"], "trades": trades, "signals": signals}


def _calc_trade_advice(df, support_levels, volatility_info):
    if df.empty:
        return None
    last_close = float(df["close"].iloc[-1])
    tier = volatility_info.get("tier", "mid_vol")
    stop_ratios = {"high_vol": 0.07, "mid_vol": 0.05, "low_vol": 0.035}
    stop_ratio = stop_ratios.get(tier, 0.05)
    support_price = support_levels[0]["price"] if support_levels else 0
    stop_by_ratio = last_close * (1 - stop_ratio)
    stop_loss = max(support_price * 0.98, stop_by_ratio) if support_price else stop_by_ratio
    take_profit = last_close + 2 * (last_close - stop_loss)
    recent_high = float(df["high"].tail(5).max())
    atr_pct = volatility_info.get("atr_pct") or 0
    atr = last_close * atr_pct / 100 if atr_pct else 0
    add_price = max(recent_high * 1.005, last_close + 0.5 * atr)
    return {
        "base_close": round(last_close, 2),
        "stop_loss": round(stop_loss, 2),
        "take_profit": round(take_profit, 2),
        "add_price": round(add_price, 2),
    }


def _diff_signals(v1_records, v2_records):
    v1_buy = {r["date"]: r for r in v1_records if r["signal"] == 1}
    v2_buy = {r["date"]: r for r in v2_records if r["signal"] == 1}
    v1_sell = {r["date"]: r for r in v1_records if r["signal"] == -1}
    v2_sell = {r["date"]: r for r in v2_records if r["signal"] == -1}
    return {
        "only_v2_buys": [v2_buy[d] for d in sorted(set(v2_buy) - set(v1_buy))],
        "only_v1_buys": [v1_buy[d] for d in sorted(set(v1_buy) - set(v2_buy))],
        "only_v2_sells": [v2_sell[d] for d in sorted(set(v2_sell) - set(v1_sell))],
        "only_v1_sells": [v1_sell[d] for d in sorted(set(v1_sell) - set(v2_sell))],
    }


@experimental_bp.route("/stock/<symbol>", methods=["GET"])
@requires_permission("stock:read")
@requires_us_market
def experimental_stock(symbol):
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    rsi_period = int(request.args.get("rsi_period", 14))
    try:
        df = fetch_stock_data(symbol, start_date, end_date)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 503
    if df.empty:
        return jsonify({"error": "未找到该股票数据"}), 404
    stock_info = get_stock_info(symbol)
    df_with_indicators = calculate_all_indicators(df, rsi_period=rsi_period)
    signals_df = generate_trading_signals_v2(df_with_indicators, {"buy_threshold": 0.08, "sell_threshold": 0.12})
    records = _signals_to_records(df_with_indicators, signals_df)
    sr_levels = find_support_resistance(df_with_indicators, n_support=1, n_resistance=1)
    volatility_info = signals_df.attrs.get("volatility_info", {})
    trade_advice = _calc_trade_advice(df_with_indicators, sr_levels["support_levels"], volatility_info)
    return jsonify(
        {
            "name": stock_info["name"] if stock_info else "",
            "symbol": symbol,
            "data": records,
            "support_levels": sr_levels["support_levels"],
            "resistance_levels": sr_levels["resistance_levels"],
            "volatility_info": volatility_info,
            "trade_advice": trade_advice,
            "summary": {
                "total": len(records),
                "buy_signals": len([r for r in records if r["signal"] == 1]),
                "sell_signals": len([r for r in records if r["signal"] == -1]),
            },
        }
    )


@experimental_bp.route("/backtest", methods=["POST"])
@requires_roles("admin", "super_admin")
@requires_us_market
def experimental_backtest():
    data = request.json or {}
    symbol = data.get("symbol", "")
    config = data.get("config", {})
    has_quota, _, _ = check_backtest_quota(g.user_id)
    if not has_quota:
        return jsonify({"error": "回测次数已用完，请升级套餐"}), 403
    result = run_backtest_v2(symbol, data.get("start_date", ""), data.get("end_date", ""), config)
    if "error" in result:
        return jsonify(result), 404
    increment_backtest_usage(g.user_id)
    add_audit_log("run_experimental_backtest", "experimental", g.user_id)
    formatted = _format_backtest_result(result)
    formatted["volatility_info"] = result.get("volatility_info", {})
    return jsonify(formatted)


@experimental_bp.route("/compare", methods=["POST"])
@requires_roles("admin", "super_admin")
@requires_us_market
def experimental_compare():
    data = request.json or {}
    symbol = data.get("symbol", "")
    start_date = data.get("start_date", "")
    end_date = data.get("end_date", "")
    config = {"initial_capital": 100000, "commission_rate": 0.001, "buy_threshold": 0.08, "sell_threshold": 0.12}
    config.update(data.get("config", {}))
    has_quota, _, _ = check_backtest_quota(g.user_id)
    if not has_quota:
        return jsonify({"error": "回测次数已用完，请升级套餐"}), 403
    df = fetch_stock_data(symbol, start_date, end_date)
    if df.empty:
        return jsonify({"error": "未找到该股票数据"}), 404
    df_with_indicators = calculate_all_indicators(df)
    v1_signals = generate_trading_signals(df_with_indicators, config)
    v2_signals = generate_trading_signals_v2(df_with_indicators, config)
    v1_records = _signals_to_records(df_with_indicators, v1_signals)
    v2_records = _signals_to_records(df_with_indicators, v2_signals)
    v1_backtest = run_backtest(symbol, start_date, end_date, config)
    v2_backtest = run_backtest_v2(symbol, start_date, end_date, config)
    if "error" in v1_backtest:
        return jsonify(v1_backtest), 404
    if "error" in v2_backtest:
        return jsonify(v2_backtest), 404
    increment_backtest_usage(g.user_id)
    add_audit_log("compare_experimental_strategy", "experimental", g.user_id)
    stock_info = get_stock_info(symbol)
    return jsonify(
        {
            "symbol": symbol,
            "name": stock_info["name"] if stock_info else "",
            "kline": v2_records,
            "volatility_info": v2_signals.attrs.get("volatility_info", {}),
            "v1": {"records": v1_records, **_format_backtest_result(v1_backtest)},
            "v2": {"records": v2_records, **_format_backtest_result(v2_backtest)},
            "diff": _diff_signals(v1_records, v2_records),
        }
    )
