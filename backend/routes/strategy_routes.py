from flask import request, jsonify, g
import pandas as pd
import requests

from routes import strategy_bp
from auth import (
    requires_permission,
    requires_backtest_quota,
    requires_us_market,
    increment_backtest_usage,
    add_audit_log,
)
from data_fetcher import fetch_stock_data, get_stock_info
from indicators import calculate_all_indicators
from strategies_custom import (
    get_strategy_templates,
    get_default_config,
    get_preset_configs,
    get_preset_config,
    generate_custom_signals,
)
from backtest import BacktestEngine
from strategy_store import (
    get_stock_strategies,
    get_default_strategy,
    save_stock_strategy,
    delete_stock_strategy,
)


@strategy_bp.route("/templates", methods=["GET"])
@requires_permission("stock:read")
def strategy_templates():
    """获取所有可用策略模板及参数定义"""
    return jsonify({"data": get_strategy_templates()})


@strategy_bp.route("/default", methods=["GET"])
@requires_permission("stock:read")
def strategy_default():
    """获取默认策略配置"""
    return jsonify({"data": get_default_config()})


@strategy_bp.route("/presets", methods=["GET"])
@requires_permission("stock:read")
def strategy_presets():
    """获取所有预设方案"""
    return jsonify({"data": get_preset_configs()})


@strategy_bp.route("/presets/<preset_key>", methods=["GET"])
@requires_permission("stock:read")
def strategy_preset_detail(preset_key):
    """获取指定预设方案的完整配置"""
    config = get_preset_config(preset_key)
    if config is None:
        return jsonify({"error": "未找到该预设方案"}), 404
    return jsonify({"data": config})


@strategy_bp.route("/stock/<symbol>", methods=["GET"])
@requires_permission("stock:read")
def get_stock_strategy_configs(symbol):
    """获取用户某只股票已保存的策略配置列表"""
    user_id = g.user_id
    if user_id is None:
        return jsonify({"data": []})
    configs = get_stock_strategies(user_id, symbol)
    return jsonify({"data": configs})


@strategy_bp.route("/stock/<symbol>", methods=["POST"])
@requires_permission("watchlist:write")
@requires_us_market
def save_stock_strategy_config(symbol):
    """保存策略配置到某只股票"""
    user_id = g.user_id
    if user_id is None:
        return jsonify({"error": "请先登录"}), 401

    data = request.json or {}
    config = data.get("config")
    config_name = data.get("config_name", "默认")
    is_default = data.get("is_default", True)
    stock_name = data.get("stock_name", "")

    if not config:
        return jsonify({"error": "缺少策略配置"}), 400

    strategy_id = save_stock_strategy(user_id, symbol, stock_name, config_name, config, is_default)
    add_audit_log("save_stock_strategy", f"strategy:{symbol}", user_id)
    return jsonify({"success": True, "id": strategy_id})


@strategy_bp.route("/stock/<symbol>", methods=["DELETE"])
@requires_permission("watchlist:write")
def delete_stock_strategy_config(symbol):
    """删除某只股票的策略配置"""
    user_id = g.user_id
    if user_id is None:
        return jsonify({"error": "请先登录"}), 401

    config_name = request.args.get("config_name", "默认")
    deleted = delete_stock_strategy(user_id, symbol, config_name)
    if not deleted:
        return jsonify({"error": "未找到该策略配置"}), 404
    add_audit_log("delete_stock_strategy", f"strategy:{symbol}", user_id)
    return jsonify({"success": True})


@strategy_bp.route("/preview", methods=["POST"])
@requires_permission("stock:read")
@requires_us_market
def strategy_preview():
    """用自定义策略配置预览买卖信号"""
    data = request.json or {}
    symbol = data.get("symbol", "")
    start_date = data.get("start_date", "")
    end_date = data.get("end_date", "")
    config = data.get("config")
    rsi_period = int(data.get("rsi_period", 14))

    if not symbol:
        return jsonify({"error": "请输入股票代码"}), 400
    if not config:
        config = get_default_config()

    try:
        df = fetch_stock_data(symbol, start_date, end_date)
    except requests.exceptions.RequestException as e:
        msg = str(e)
        status = 503
        if "限流" in msg or "429" in msg or "rate" in msg.lower():
            status = 429
        return jsonify({"error": msg}), status

    if df.empty:
        return jsonify({"error": "未找到该股票数据"}), 404

    # 回测只用 T-1 已收盘数据
    from datetime import datetime

    today = pd.Timestamp(datetime.now().date())
    if not df.empty and df.index[-1].date() >= today.date():
        df = df.iloc[:-1]

    if df.empty:
        return jsonify({"error": "未找到该股票数据"}), 404

    df_with_indicators = calculate_all_indicators(df, rsi_period=rsi_period)
    signals_df = generate_custom_signals(df_with_indicators, config)

    result_df = df_with_indicators.copy()
    for col in ["buy_score", "sell_score", "signal"]:
        result_df[col] = signals_df[col]

    records = []
    for date, row in result_df.iterrows():
        records.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "close": round(row["close"], 2),
                "signal": int(row["signal"]),
                "buy_score": round(row["buy_score"], 3),
                "sell_score": round(row["sell_score"], 3),
            }
        )

    buy_points = [r for r in records if r["signal"] == 1]
    sell_points = [r for r in records if r["signal"] == -1]

    return jsonify(
        {
            "symbol": symbol,
            "data": records,
            "summary": {
                "total": len(records),
                "buy_signals": len(buy_points),
                "sell_signals": len(sell_points),
            },
        }
    )


@strategy_bp.route("/backtest", methods=["POST"])
@requires_backtest_quota
@requires_us_market
def strategy_backtest():
    """用自定义策略配置运行回测"""
    data = request.json or {}
    symbol = data.get("symbol", "")
    start_date = data.get("start_date", "")
    end_date = data.get("end_date", "")
    config = data.get("config")
    rsi_period = int(data.get("rsi_period", 14))

    if not symbol:
        return jsonify({"error": "请输入股票代码"}), 400
    if not config:
        config = get_default_config()

    try:
        df = fetch_stock_data(symbol, start_date, end_date)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 503

    if df.empty:
        return jsonify({"error": "未找到该股票数据"}), 404

    # 回测只用 T-1 已收盘数据
    from datetime import datetime

    today = pd.Timestamp(datetime.now().date())
    if not df.empty and df.index[-1].date() >= today.date():
        df = df.iloc[:-1]

    if df.empty:
        return jsonify({"error": "未找到该股票数据"}), 404

    df_with_indicators = calculate_all_indicators(df, rsi_period=rsi_period)
    signals_df = generate_custom_signals(df_with_indicators, config)

    # 运行回测
    engine = BacktestEngine(
        initial_capital=config.get("initial_capital", 100000),
        commission_rate=config.get("commission_rate", 0.001),
    )
    result = engine.run(df_with_indicators, signals_df)

    increment_backtest_usage(g.user_id)
    add_audit_log("run_custom_backtest", f"strategy:{symbol}", g.user_id)

    # 格式化输出
    trades = []
    for t in result["trades"]:
        trade = {k: v for k, v in t.items()}
        if "date" in trade:
            trade["date"] = (
                trade["date"].strftime("%Y-%m-%d") if hasattr(trade["date"], "strftime") else str(trade["date"])
            )
        trades.append(trade)

    equity_curve = []
    for e in result["equity_curve"]:
        ec = {k: v for k, v in e.items()}
        if "date" in ec:
            ec["date"] = ec["date"].strftime("%Y-%m-%d") if hasattr(ec["date"], "strftime") else str(ec["date"])
        equity_curve.append(ec)

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

    return jsonify(
        {
            "metrics": result["metrics"],
            "trades": trades,
            "equity_curve": equity_curve,
            "signals": signals,
        }
    )
