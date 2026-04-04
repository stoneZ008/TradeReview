import pandas as pd
import numpy as np
from indicators import calculate_all_indicators
from strategies import generate_trading_signals

class BacktestEngine:
    """
    回测引擎
    """
    def __init__(self, initial_capital=100000, commission_rate=0.001):
        """
        参数:
            initial_capital: 初始资金
            commission_rate: 手续费率
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
    
    def run(self, df, signals_df):
        """
        运行回测
        
        参数:
            df: 原始OHLCV数据（包含技术指标）
            signals_df: 包含signal列的DataFrame
        
        返回:
            回测结果DataFrame
        """
        result = df.copy()
        result['signal'] = signals_df['signal']
        result['buy_score'] = signals_df['buy_score']
        result['sell_score'] = signals_df['sell_score']
        
        # 初始化变量
        capital = self.initial_capital
        position = 0  # 持有股数
        buy_price = 0
        
        # 记录交易
        trades = []
        equity_curve = []
        
        for i, (date, row) in enumerate(result.iterrows()):
            signal = row['signal']
            price = row['close']
            
            # 过滤买入信号：signal == 1 (已通过阈值筛选)
            valid_buy = signal == 1
            
            # 过滤卖出信号：signal == -1 且 跌破MA5（与K线图显示一致）
            ma5 = row.get('ma5', 0)
            valid_sell = signal == -1 and price < ma5
            
            # 执行交易
            if valid_buy and position == 0:  # 买入信号且空仓
                # 全仓买入（支持按股买入，不强制按手）
                cost = capital * 0.95
                shares = int(cost / price)
                if shares > 0:
                    cost = shares * price * (1 + self.commission_rate)
                    capital -= cost
                    position = shares
                    buy_price = price
                    trades.append({
                        'date': date,
                        'type': 'buy',
                        'price': price,
                        'shares': shares,
                        'cost': cost,
                        'signal_score': row['buy_score']
                    })
            
            elif valid_sell and position > 0:  # 卖出信号且持仓
                # 检查MA5有效性，如果MA5<=0则只用信号判断
                ma5_valid = ma5 > 0
                sell_condition = valid_sell
                if ma5_valid:
                    sell_condition = valid_sell  # 已经在valid_sell中判断了price<ma5
                
                if sell_condition:
                    # 全部卖出
                    revenue = position * price * (1 - self.commission_rate)
                    profit = revenue - position * buy_price * (1 + self.commission_rate)
                    profit_pct = (price - buy_price) / buy_price * 100
                    
                    trades.append({
                        'date': date,
                        'type': 'sell',
                        'price': price,
                        'shares': position,
                        'revenue': revenue,
                        'profit': profit,
                        'profit_pct': profit_pct,
                        'signal_score': row['sell_score']
                    })
                    
                    capital += revenue
                    position = 0
                    buy_price = 0
            
            # 计算当前权益
            total_equity = capital + position * price
            equity_curve.append({
                'date': date,
                'equity': total_equity,
                'capital': capital,
                'position_value': position * price,
                'position': position
            })
        
        # 如果最后一天还有持仓，计算最终收益
        if position > 0:
            final_price = result['close'].iloc[-1]
            revenue = position * final_price * (1 - self.commission_rate)
            capital += revenue
        
        # 计算回测指标
        metrics = self.calculate_metrics(trades, equity_curve)
        
        # 返回结果
        return {
            'signals': result,
            'trades': trades,
            'equity_curve': equity_curve,
            'metrics': metrics
        }
    
    def calculate_metrics(self, trades, equity_curve):
        """
        计算回测指标
        """
        # 基础数据
        initial_capital = self.initial_capital
        final_equity = equity_curve[-1]['equity'] if equity_curve else initial_capital
        
        if not trades:
            return {
                'total_return': 0,
                'annual_return': 0,
                'max_drawdown': 0,
                'win_rate': 0,
                'total_trades': 0,
                'buy_trades': 0,
                'avg_profit': 0,
                'avg_loss': 0,
                'profit_loss_ratio': 0,
                'sharpe_ratio': 0,
                'initial_capital': initial_capital,
                'final_equity': final_equity
            }
        
        # 筛选卖出交易
        sell_trades = [t for t in trades if t['type'] == 'sell']
        
        # 总收益率
        final_equity = equity_curve[-1]['equity']
        total_return = (final_equity - self.initial_capital) / self.initial_capital * 100
        
        # 年化收益率（假设250个交易日）
        days = len(equity_curve)
        if days > 0:
            annual_return = ((1 + total_return/100) ** (250/days) - 1) * 100
        else:
            annual_return = 0
        
        # 最大回撤
        equity_series = pd.Series([e['equity'] for e in equity_curve])
        rolling_max = equity_series.expanding().max()
        drawdown = (equity_series - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()
        
        # 胜率
        if sell_trades:
            winning_trades = [t for t in sell_trades if t.get('profit', 0) > 0]
            losing_trades = [t for t in sell_trades if t.get('profit', 0) <= 0]
            win_rate = len(winning_trades) / len(sell_trades) * 100
            
            # 平均盈利/亏损
            avg_profit = np.mean([t.get('profit_pct', 0) for t in winning_trades]) if winning_trades else 0
            avg_loss = np.mean([abs(t.get('profit_pct', 0)) for t in losing_trades]) if losing_trades else 0
            
            # 盈亏比
            profit_loss_ratio = avg_profit / avg_loss if avg_loss > 0 else 0
        else:
            win_rate = 0
            avg_profit = 0
            avg_loss = 0
            profit_loss_ratio = 0
        
        # Sharpe Ratio（简化版）
        if len(equity_curve) > 1:
            returns = equity_series.pct_change().dropna()
            if returns.std() > 0:
                sharpe_ratio = returns.mean() / returns.std() * np.sqrt(250)
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        return {
            'total_return': round(total_return, 2),
            'annual_return': round(annual_return, 2),
            'max_drawdown': round(max_drawdown, 2),
            'win_rate': round(win_rate, 2),
            'total_trades': len(sell_trades),
            'buy_trades': len([t for t in trades if t['type'] == 'buy']),
            'avg_profit': round(avg_profit, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_loss_ratio': round(profit_loss_ratio, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'initial_capital': self.initial_capital,
            'final_equity': round(equity_curve[-1]['equity'], 2) if equity_curve else 0
        }


def run_backtest(symbol, start_date, end_date, config=None):
    """
    运行完整回测流程
    
    参数:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        config: 策略配置
    
    返回:
        回测结果
    """
    from data_fetcher import fetch_stock_data
    
    # 获取数据
    df = fetch_stock_data(symbol, start_date, end_date)
    
    if df.empty:
        return {'error': '无法获取数据'}
    
    # 计算技术指标
    df_with_indicators = calculate_all_indicators(df)
    
    # 生成信号
    signals_df = generate_trading_signals(df_with_indicators, config)
    
    # 运行回测
    engine = BacktestEngine(
        initial_capital=config.get('initial_capital', 100000) if config else 100000,
        commission_rate=config.get('commission_rate', 0.001) if config else 0.001
    )
    
    result = engine.run(df_with_indicators, signals_df)
    
    return result
