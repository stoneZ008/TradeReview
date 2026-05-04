from functools import wraps
from flask import request, jsonify, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from user_db import get_connection
from data_fetcher import is_us_stock
import json

def get_user_permissions(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT p.name FROM permissions p
        JOIN role_permissions rp ON p.id = rp.permission_id
        JOIN user_roles ur ON rp.role_id = ur.role_id
        WHERE ur.user_id = ?
    ''', (user_id,))
    permissions = [row[0] for row in cursor.fetchall()]
    conn.close()
    return permissions

def get_user_roles(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.name FROM roles r
        JOIN user_roles ur ON r.id = ur.role_id
        WHERE ur.user_id = ?
    ''', (user_id,))
    roles = [row[0] for row in cursor.fetchall()]
    conn.close()
    return roles

def get_user_subscription(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT sp.*, s.start_date, s.end_date, s.status FROM subscriptions s
        JOIN subscription_plans sp ON s.plan_id = sp.id
        WHERE s.user_id = ? AND s.status = 'active'
        ORDER BY s.end_date DESC LIMIT 1
    ''', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def is_trial_active(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT trial_end_at FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row['trial_end_at']:
        from datetime import datetime
        trial_end = datetime.fromisoformat(row['trial_end_at'])
        return datetime.now() < trial_end
    return False

def jwt_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = int(get_jwt_identity())
            g.user_id = user_id
            g.user_roles = get_user_roles(user_id)
            g.user_permissions = get_user_permissions(user_id)
            g.user_subscription = get_user_subscription(user_id)
            g.is_trial = is_trial_active(user_id)
        except Exception as e:
            return jsonify({'error': '无效或已过期的token'}), 401
        return fn(*args, **kwargs)
    return wrapper

def optional_jwt(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            if user_id:
                user_id = int(user_id)
                g.user_id = user_id
                g.user_roles = get_user_roles(user_id)
                g.user_permissions = get_user_permissions(user_id)
                g.user_subscription = get_user_subscription(user_id)
                g.is_trial = is_trial_active(user_id)
            else:
                g.user_id = None
                g.user_roles = ['guest']
                g.user_permissions = get_guest_permissions()
                g.user_subscription = None
                g.is_trial = False
        except:
            g.user_id = None
            g.user_roles = ['guest']
            g.user_permissions = get_guest_permissions()
            g.user_subscription = None
            g.is_trial = False
        return fn(*args, **kwargs)
    return wrapper

def get_guest_permissions():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT p.name FROM permissions p
        JOIN role_permissions rp ON p.id = rp.permission_id
        JOIN roles r ON rp.role_id = r.id
        WHERE r.name = 'guest'
    ''')
    permissions = [row[0] for row in cursor.fetchall()]
    conn.close()
    return permissions

def requires_roles(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        @jwt_required
        def wrapper(*args, **kwargs):
            user_roles = g.user_roles
            if not any(role in allowed_roles for role in user_roles):
                return jsonify({'error': '权限不足'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def requires_permission(permission):
    def decorator(fn):
        @wraps(fn)
        @optional_jwt
        def wrapper(*args, **kwargs):
            if permission not in g.user_permissions:
                return jsonify({'error': '权限不足'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def check_backtest_quota(user_id):
    if user_id is None:
        return False, 0, 0
    
    subscription = get_user_subscription(user_id)
    trial = is_trial_active(user_id)
    
    if trial:
        max_backtests = 10
    elif subscription:
        max_backtests = subscription['max_backtests_monthly']
    else:
        max_backtests = 0
    
    if max_backtests == -1:
        return True, -1, 0
    
    from datetime import datetime
    month = datetime.now().strftime('%Y-%m')
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT count FROM backtest_usage WHERE user_id = ? AND month = ?', (user_id, month))
    row = cursor.fetchone()
    used = row['count'] if row else 0
    conn.close()
    
    remaining = max_backtests - used
    return remaining > 0, max_backtests, used

def increment_backtest_usage(user_id):
    from datetime import datetime
    month = datetime.now().strftime('%Y-%m')
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO backtest_usage (user_id, count, month)
        VALUES (?, 1, ?)
        ON CONFLICT(user_id, month) DO UPDATE SET count = count + 1
    ''', (user_id, month))
    conn.commit()
    conn.close()

def requires_backtest_quota(fn):
    @wraps(fn)
    @jwt_required
    def wrapper(*args, **kwargs):
        has_quota, max_quota, used = check_backtest_quota(g.user_id)
        if not has_quota:
            return jsonify({'error': '回测次数已用完，请升级套餐'}), 403
        return fn(*args, **kwargs)
    return wrapper

def add_audit_log(action, resource=None, user_id=None):
    ip_address = request.remote_addr if request else None
    user_agent = request.user_agent.string if request and request.user_agent else None
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO audit_logs (user_id, action, resource, ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, action, resource, ip_address, user_agent))
    conn.commit()
    conn.close()


def has_us_stock_permission(user_id):
    """检查用户是否有权限访问美股（仅企业版订阅）"""
    subscription = get_user_subscription(user_id)
    # 企业版名称是 'enterprise'
    if subscription and subscription['name'] == 'enterprise':
        return True
    return False


def requires_us_market(fn):
    """装饰器：检查用户是否有权限访问美股"""
    @wraps(fn)
    @optional_jwt
    def wrapper(*args, **kwargs):
        # 从 URL 参数或请求体中获取股票代码
        symbol = kwargs.get('symbol', '')
        if not symbol and request.method == 'POST':
            data = request.get_json(silent=True) or {}
            symbol = data.get('symbol', '')
        
        # 如果是美股，检查订阅权限
        if symbol and is_us_stock(symbol):
            if not g.user_id:
                return jsonify({'error': '请先登录'}), 401
            if not has_us_stock_permission(g.user_id):
                return jsonify({'error': '美股功能仅限企业版订阅用户使用'}), 403
        
        return fn(*args, **kwargs)
    return wrapper
