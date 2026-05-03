from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
import pandas as pd
import json
import requests
import os
import sqlite3
from datetime import timedelta

from data_fetcher import fetch_stock_data, search_stock, get_stock_info
from indicators import calculate_all_indicators
from strategies import generate_trading_signals
from backtest import run_backtest
from industry_db import seed_default_data, get_all_industries, add_industry, update_industry, add_sub_industry, update_sub_industry, add_company, update_company, delete_company
from user_db import seed_initial_data, get_connection
from user_service import create_user, authenticate_user, get_user_by_id, change_password, update_profile, get_all_users, assign_user_role, get_all_plans, assign_subscription
from auth import jwt_required, optional_jwt, requires_roles, requires_permission, requires_backtest_quota, check_backtest_quota, increment_backtest_usage, add_audit_log

app = Flask(__name__)
CORS(app)

app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'trade-review-secret-key-2024')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

jwt = JWTManager(app)
bcrypt = Bcrypt(app)

seed_default_data()
seed_initial_data()

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '')
    email = data.get('email', '')
    password = data.get('password', '')
    
    if not username or not email or not password:
        return jsonify({'error': '请填写完整信息'}), 400
    
    if len(password) < 6:
        return jsonify({'error': '密码长度至少6位'}), 400
    
    user, err = create_user(username, email, password)
    if err:
        return jsonify({'error': err}), 400
    
    result, err = authenticate_user(username, password)
    if err:
        return jsonify({'error': err}), 400
    
    return jsonify(result)

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '')
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': '请输入用户名和密码'}), 400
    
    result, err = authenticate_user(username, password)
    if err:
        return jsonify({'error': err}), 401
    
    return jsonify(result)

@app.route('/api/auth/refresh', methods=['POST'])
@jwt_required
def refresh():
    from flask_jwt_extended import create_access_token
    new_token = create_access_token(identity=str(g.user_id))
    return jsonify({'access_token': new_token})

@app.route('/api/auth/profile', methods=['GET'])
@jwt_required
def get_profile():
    user = get_user_by_id(g.user_id)
    has_quota, max_quota, used = check_backtest_quota(g.user_id)
    user['backtest_quota'] = {
        'max': max_quota,
        'used': used,
        'remaining': max_quota - used if max_quota != -1 else -1
    }
    return jsonify(user)

@app.route('/api/auth/profile', methods=['PUT'])
@jwt_required
def put_profile():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    
    user, err = update_profile(g.user_id, username, email)
    if err:
        return jsonify({'error': err}), 400
    return jsonify(user)

@app.route('/api/auth/change-password', methods=['POST'])
@jwt_required
def post_change_password():
    data = request.json
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    
    if len(new_password) < 6:
        return jsonify({'error': '新密码长度至少6位'}), 400
    
    success, err = change_password(g.user_id, old_password, new_password)
    if not success:
        return jsonify({'error': err}), 400
    return jsonify({'success': True})

@app.route('/api/billing/plans', methods=['GET'])
def get_plans():
    return jsonify({'data': get_all_plans()})

@app.route('/api/billing/my-subscription', methods=['GET'])
@jwt_required
def get_my_subscription():
    from auth import get_user_subscription
    subscription = get_user_subscription(g.user_id)
    has_quota, max_quota, used = check_backtest_quota(g.user_id)
    return jsonify({
        'subscription': subscription,
        'backtest_quota': {
            'max': max_quota,
            'used': used,
            'remaining': max_quota - used if max_quota != -1 else -1
        }
    })

@app.route('/api/admin/users', methods=['GET'])
@requires_roles('super_admin', 'admin')
def admin_list_users():
    users = get_all_users()
    return jsonify({'data': users})

@app.route('/api/admin/users/<int:user_id>/subscription', methods=['PUT'])
@requires_roles('super_admin', 'admin')
def admin_assign_subscription(user_id):
    data = request.json
    plan_name = data.get('plan_name', '')
    is_yearly = data.get('is_yearly', False)
    
    if not plan_name:
        return jsonify({'error': '请指定套餐'}), 400
    
    success, err = assign_subscription(g.user_id, user_id, plan_name, is_yearly)
    if not success:
        return jsonify({'error': err}), 400
    return jsonify({'success': True})

@app.route('/api/admin/users/<int:user_id>/roles', methods=['PUT'])
@requires_roles('super_admin')
def admin_assign_role(user_id):
    data = request.json
    role_name = data.get('role_name', '')
    
    if not role_name:
        return jsonify({'error': '请指定角色'}), 400
    
    success, err = assign_user_role(user_id, role_name)
    if not success:
        return jsonify({'error': err}), 400
    return jsonify({'success': True})

@app.route('/api/admin/audit-logs', methods=['GET'])
@requires_roles('super_admin', 'admin')
def admin_audit_logs():
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT a.*, u.username FROM audit_logs a
        LEFT JOIN users u ON a.user_id = u.id
        ORDER BY a.created_at DESC LIMIT ? OFFSET ?
    ''', (limit, offset))
    rows = cursor.fetchall()
    conn.close()
    
    return jsonify({'data': [dict(row) for row in rows]})

@app.route('/api/search', methods=['GET'])
def search():
    """搜索股票"""
    keyword = request.args.get('keyword', '')
    df = search_stock(keyword)
    if df.empty:
        return jsonify({'data': []})
    return jsonify({'data': df.to_dict(orient='records')})

@app.route('/api/stock/<symbol>', methods=['GET'])
@requires_permission('stock:read')
def get_stock_data(symbol):
    """获取股票历史数据和技术指标"""
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    try:
        df = fetch_stock_data(symbol, start_date, end_date)
    except requests.exceptions.RequestException:
        return jsonify({'error': '数据源网络异常，请稍后重试'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    if df.empty:
        return jsonify({'error': '未找到该股票数据'}), 404
    
    # 获取股票名称
    stock_info = get_stock_info(symbol)
    stock_name = stock_info['name'] if stock_info else ''
    
    # 计算技术指标
    df_with_indicators = calculate_all_indicators(df)
    
    # 生成信号（与回测API一致，卖出阈值0.12）
    signals_df = generate_trading_signals(df_with_indicators, {'buy_threshold': 0.08, 'sell_threshold': 0.12})
    
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
@requires_backtest_quota
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
        
        increment_backtest_usage(g.user_id)
        add_audit_log('run_backtest', 'backtest', g.user_id)
        
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
@requires_permission('stock:read')
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
@requires_permission('watchlist:read')
def get_watchlist():
    user_id = g.user_id if g.user_id else None
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT stock_code, stock_name FROM user_watchlists
        WHERE user_id = ? ORDER BY created_at DESC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    watchlist = [{'code': row['stock_code'], 'name': row['stock_name']} for row in rows]
    return jsonify({'data': watchlist})

@app.route('/api/watchlist', methods=['POST'])
@requires_permission('watchlist:write')
def add_watchlist():
    data = request.json
    code = data.get('code', '')
    name = data.get('name', '')
    user_id = g.user_id
    
    if not code or not name:
        return jsonify({'error': '缺少代码或名称'}), 400
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO user_watchlists (user_id, stock_code, stock_name)
            VALUES (?, ?, ?)
        ''', (user_id, code, name))
        conn.commit()
        message = '添加成功'
    except sqlite3.IntegrityError:
        message = '该股票已在自选股中'
    conn.close()
    
    result = get_watchlist()
    response = result.get_json()
    response['success'] = True
    response['message'] = message
    return jsonify(response)

@app.route('/api/watchlist/<code>', methods=['DELETE'])
@requires_permission('watchlist:write')
def delete_watchlist(code):
    user_id = g.user_id
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_watchlists WHERE user_id = ? AND stock_code = ?', (user_id, code))
    conn.commit()
    conn.close()
    
    result = get_watchlist()
    response = result.get_json()
    response['success'] = True
    response['message'] = '删除成功'
    return jsonify(response)

# ========== 行业分类 ==========

@app.route('/api/industries', methods=['GET'])
@requires_permission('industry:read')
def get_industries():
    return jsonify({'data': get_all_industries()})

@app.route('/api/industries', methods=['POST'])
@requires_permission('industry:write')
def create_industry():
    data = request.json
    name = data.get('name', '')
    icon = data.get('icon', '🏢')
    if not name:
        return jsonify({'success': False, 'error': '请输入行业名称'}), 400
    try:
        industry_id = add_industry(name, icon)
        return jsonify({'success': True, 'id': industry_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/industries/<int:industry_id>', methods=['PUT'])
@requires_permission('industry:write')
def edit_industry(industry_id):
    data = request.json
    name = data.get('name', '')
    icon = data.get('icon', '🏢')
    if not name:
        return jsonify({'success': False, 'error': '请输入行业名称'}), 400
    try:
        update_industry(industry_id, name, icon)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sub-industries', methods=['POST'])
@requires_permission('industry:write')
def create_sub_industry():
    data = request.json
    industry_id = data.get('industry_id')
    name = data.get('name', '')
    if not industry_id or not name:
        return jsonify({'success': False, 'error': '参数不完整'}), 400
    try:
        sub_id = add_sub_industry(industry_id, name)
        return jsonify({'success': True, 'id': sub_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sub-industries/<int:sub_id>', methods=['PUT'])
@requires_permission('industry:write')
def edit_sub_industry(sub_id):
    data = request.json
    name = data.get('name', '')
    if not name:
        return jsonify({'success': False, 'error': '请输入子行业名称'}), 400
    try:
        update_sub_industry(sub_id, name)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/companies', methods=['POST'])
@requires_permission('industry:write')
def create_company():
    data = request.json
    sub_industry_id = data.get('sub_industry_id')
    code = data.get('code', '')
    name = data.get('name', '')
    role = data.get('role', '')
    feature = data.get('feature', '')
    description = data.get('description', '')
    if not sub_industry_id or not code or not name:
        return jsonify({'success': False, 'error': '缺少公司代码或名称'}), 400
    try:
        company_id = add_company(sub_industry_id, code, name, role, feature, description)
        return jsonify({'success': True, 'id': company_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/companies/<int:company_id>', methods=['PUT'])
@requires_permission('industry:write')
def edit_company(company_id):
    data = request.json
    code = data.get('code', '')
    name = data.get('name', '')
    role = data.get('role', '')
    feature = data.get('feature', '')
    description = data.get('description', '')
    if not code or not name:
        return jsonify({'success': False, 'error': '缺少公司代码或名称'}), 400
    try:
        update_company(company_id, code, name, role, feature, description)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/companies/<int:company_id>', methods=['DELETE'])
@requires_permission('industry:write')
def remove_company(company_id):
    try:
        delete_company(company_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/subscription/plans', methods=['GET'])
@optional_jwt
def get_subscription_plans():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name, monthly_price, yearly_price, 
               max_backtests_monthly, features_json, description
        FROM subscription_plans
        ORDER BY monthly_price
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    plans = []
    for row in rows:
        features = json.loads(row['features_json']) if row['features_json'] else {}
        plans.append({
            'id': row['id'],
            'name': row['name'],
            'name_cn': {'trial': '试用版', 'basic': '基础版', 'pro': '专业版', 'enterprise': '企业版'}.get(row['name'], row['name']),
            'monthly_price': row['monthly_price'],
            'yearly_price': row['yearly_price'],
            'max_backtests_monthly': row['max_backtests_monthly'],
            'features': features,
            'description': row['description']
        })
    
    return jsonify({'data': plans})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
