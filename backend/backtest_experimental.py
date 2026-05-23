import pandas as pd
from indicators import calculate_all_indicators
from strategies_experimental import generate_trading_signals_v2
from backtest import BacktestEngine


def run_backtest_v2(symbol, start_date, end_date, config=None):
    from data_fetcher import fetch_stock_data
    from datetime import datetime

    if config is None:
        config = {}

    df = fetch_stock_data(symbol, start_date, end_date)
    if df.empty:
        return {"error": "无法获取数据"}

    today = pd.Timestamp(datetime.now().date())
    if not df.empty and df.index[-1].date() >= today.date():
        df = df.iloc[:-1]

    if df.empty:
        return {"error": "无法获取数据"}

    df_with_indicators = calculate_all_indicators(df)
    signals_df = generate_trading_signals_v2(df_with_indicators, config)
    engine = BacktestEngine(
        initial_capital=config.get("initial_capital", 100000),
        commission_rate=config.get("commission_rate", 0.001),
    )
    result = engine.run(df_with_indicators, signals_df)
    result["volatility_info"] = signals_df.attrs.get("volatility_info", {})
    return result
