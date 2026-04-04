from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import json

from data_fetcher import fetch_stock_data, search_stock, get_stock_info
from indicators import calculate_all_indicators
from strategies import generate_trading_signals
from backtest import run_backtest
from watchlist_manager import load_watchlist, add_to_watchlist, remove_from_watchlist

app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/api/search', methods=['GET'])
def search():
    """搜索股票"""
    keyword = request.args.get('keyword', '')
    df = search_stock(keyword)
    if df.empty:
        return jsonify({'data': []})
    return jsonify({'data': df.to_dict(orient='records')})

@app.route('/api/stock/<symbol>', methods=['GET'])
def get_stock_data(symbol):
    """获取股票历史数据和技术指标"""
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # 为了正确计算技术指标，需要获取额外的历史数据
    # MA60需要60天，MACD需要26天EMA，KDJ需要9天
    # 额外获取60天历史数据确保指标准确
    from datetime import datetime, timedelta
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y%m%d')
            # 提前60个交易日（约3个月）
            extended_start = (start_dt - timedelta(days=90)).strftime('%Y%m%d')
        except:
            extended_start = start_date
    else:
        extended_start = start_date
    
    # 获取包含历史数据的数据
    df_full = fetch_stock_data(symbol, extended_start, end_date)
    
    if df_full.empty:
        return jsonify({'error': '无法获取数据'}), 404
    
    # 获取股票名称
    stock_info = get_stock_info(symbol)
    stock_name = stock_info['name'] if stock_info else ''
    
    # 计算技术指标（使用完整数据）
    df_with_indicators = calculate_all_indicators(df_full)
    
    # 生成信号（使用完整数据）
    signals_df = generate_trading_signals(df_with_indicators, {'buy_threshold': 0.08, 'sell_threshold': 0.08})
    
    # 过滤到用户请求的日期范围
    if start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y%m%d')
            end_dt = datetime.strptime(end_date, '%Y%m%d')
            mask = (df_with_indicators.index >= start_dt) & (df_with_indicators.index <= end_dt)
            df_with_indicators = df_with_indicators[mask]
            signals_df = signals_df[mask]
        except:
            pass
    
    # 合并结果
    result_df = df_with_indicators.copy()
    for col in ['buy_score', 'sell_score', 'signal']:
        result_df[col] = signals_df[col]
    
    # 转换为JSON格式
    records = []
    for date, row in result_df.iterrows():
        record = {
            'date': date.strftime('%Y-%m-%d'),
            'open': round(row['open'], 2),
            'high': round(row['high'], 2),
            'low': round(row['low'], 2),
            'close': round(row['close'], 2),
            'volume': int(row['volume']),
            'ma5': round(row['ma5'], 2) if pd.notna(row['ma5']) else None,
            'ma10': round(row['ma10'], 2) if pd.notna(row['ma10']) else None,
            'ma20': round(row['ma20'], 2) if pd.notna(row['ma20']) else None,
            'ma60': round(row['ma60'], 2) if pd.notna(row['ma60']) else None,
            'boll_upper': round(row['boll_upper'], 2) if pd.notna(row['boll_upper']) else None,
            'boll_middle': round(row['boll_middle'], 2) if pd.notna(row['boll_middle']) else None,
            'boll_lower': round(row['boll_lower'], 2) if pd.notna(row['boll_lower']) else None,
            'macd': round(row['macd'], 4) if pd.notna(row['macd']) else None,
            'macd_signal': round(row['macd_signal'], 4) if pd.notna(row['macd_signal']) else None,
            'macd_hist': round(row['macd_hist'], 4) if pd.notna(row['macd_hist']) else None,
            'rsi': round(row['rsi'], 2) if pd.notna(row['rsi']) else None,
            'kdj_k': round(row['kdj_k'], 2) if pd.notna(row['kdj_k']) else None,
            'kdj_d': round(row['kdj_d'], 2) if pd.notna(row['kdj_d']) else None,
            'kdj_j': round(row['kdj_j'], 2) if pd.notna(row['kdj_j']) else None,
            'vol_ratio': round(row['vol_ratio'], 2) if pd.notna(row['vol_ratio']) else None,
            'buy_score': round(row['buy_score'], 3),
            'sell_score': round(row['sell_score'], 3),
            'signal': int(row['signal']),
            'kline_pattern': row.get('kline_pattern', ''),
            'candle_pattern': row.get('candle_pattern', '')
        }
        records.append(record)
    
    # 提取买卖点
    buy_points = [r for r in records if r['signal'] == 1]
    sell_points = [r for r in records if r['signal'] == -1]
    
    return jsonify({
        'name': stock_name,
        'symbol': symbol,
        'data': records,
        'summary': {
            'total': len(records),
            'buy_signals': len(buy_points),
            'sell_signals': len(sell_points)
        }
    })

@app.route('/api/backtest', methods=['POST'])
def backtest():
    """运行回测"""
    data = request.json
    symbol = data.get('symbol', '')
    start_date = data.get('start_date', '')
    end_date = data.get('end_date', '')
    config = data.get('config', {})
    
    # 设置默认阈值（降低阈值以便更容易产生信号）
    config.setdefault('buy_threshold', 0.08)
    config.setdefault('sell_threshold', 0.08)
    
    if not symbol:
        return jsonify({'error': '请输入股票代码'}), 400
    
    try:
        result = run_backtest(symbol, start_date, end_date, config)
        
        if 'error' in result:
            return jsonify(result), 404
        
        # 处理trades中的日期
        trades = []
        for t in result['trades']:
            trade = {k: v for k, v in t.items()}
            if 'date' in trade:
                trade['date'] = trade['date'].strftime('%Y-%m-%d') if hasattr(trade['date'], 'strftime') else str(trade['date'])
            trades.append(trade)
        
        # 处理equity_curve中的日期
        equity_curve = []
        for e in result['equity_curve']:
            ec = {k: v for k, v in e.items()}
            if 'date' in ec:
                ec['date'] = ec['date'].strftime('%Y-%m-%d') if hasattr(ec['date'], 'strftime') else str(ec['date'])
            equity_curve.append(ec)
        
        # 处理signals中的日期
        signals = []
        for date, row in result['signals'].iterrows():
            sig = {
                'date': date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date),
                'close': round(row['close'], 2),
                'signal': int(row['signal']),
                'buy_score': round(row['buy_score'], 3),
                'sell_score': round(row['sell_score'], 3),
                'ma5': round(row['ma5'], 2) if pd.notna(row.get('ma5', 0)) else 0
            }
            signals.append(sig)
        
        return jsonify({
            'metrics': result['metrics'],
            'trades': trades,
            'equity_curve': equity_curve,
            'signals': signals
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/indicators', methods=['POST'])
def get_indicators():
    """获取技术指标详情"""
    data = request.json
    symbol = data.get('symbol', '')
    start_date = data.get('start_date', '')
    end_date = data.get('end_date', '')
    indicator = data.get('indicator', 'all')
    
    df = fetch_stock_data(symbol, start_date, end_date)
    
    if df.empty:
        return jsonify({'error': '无法获取数据'}), 404
    
    df_with_indicators = calculate_all_indicators(df)
    
    # 只返回指定指标
    columns = ['open', 'high', 'low', 'close', 'volume']
    
    if indicator == 'all' or indicator == 'macd':
        columns.extend(['macd', 'macd_signal', 'macd_hist'])
    if indicator == 'all' or indicator == 'boll':
        columns.extend(['boll_upper', 'boll_middle', 'boll_lower'])
    if indicator == 'all' or indicator == 'rsi':
        columns.append('rsi')
    if indicator == 'all' or indicator == 'kdj':
        columns.extend(['kdj_k', 'kdj_d', 'kdj_j'])
    
    records = []
    for date, row in df_with_indicators[columns].iterrows():
        record = {'date': date.strftime('%Y-%m-%d')}
        for col in columns:
            val = row[col]
            if pd.notna(val):
                record[col] = round(float(val), 4)
            else:
                record[col] = None
        records.append(record)
    
    return jsonify({'data': records})

@app.route('/api/watchlist', methods=['GET'])
def get_watchlist():
    """获取自选股列表"""
    watchlist = load_watchlist()
    return jsonify({'data': watchlist})

@app.route('/api/watchlist', methods=['POST'])
def add_watchlist():
    """添加股票到自选股"""
    data = request.json
    code = data.get('code', '')
    name = data.get('name', '')
    
    if not code or not name:
        return jsonify({'error': '缺少代码或名称'}), 400
    
    success, message = add_to_watchlist({'code': code, 'name': name})
    
    if success:
        return jsonify({'success': True, 'message': message, 'data': load_watchlist()})
    else:
        return jsonify({'success': False, 'message': message}), 400

@app.route('/api/watchlist/<code>', methods=['DELETE'])
def delete_watchlist(code):
    """从自选股删除股票"""
    success, message = remove_from_watchlist(code)
    
    if success:
        return jsonify({'success': True, 'message': message, 'data': load_watchlist()})
    else:
        return jsonify({'success': False, 'message': message}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
