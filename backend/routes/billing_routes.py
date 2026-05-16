from flask import request, jsonify, g
import json
import os

from routes import billing_bp
from user_db import get_connection
from user_service import get_all_plans
from auth import jwt_required, optional_jwt, check_backtest_quota, get_user_subscription


@billing_bp.route('/billing/plans', methods=['GET'])
def get_plans():
    return jsonify({'data': get_all_plans()})


@billing_bp.route('/billing/my-subscription', methods=['GET'])
@jwt_required
def get_my_subscription():
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


ZSXQ_GROUP_NAME = os.environ.get('ZSXQ_GROUP_NAME', 'TradeReview 交易复盘')
ZSXQ_JOIN_URL = os.environ.get('ZSXQ_JOIN_URL', 'https://t.zsxq.com/your-invite-code')
ZSXQ_QR_URL = os.environ.get('ZSXQ_QR_URL', '')
ZSXQ_CONTACT = os.environ.get('ZSXQ_CONTACT', '加入知识星球后，请将昵称/星球账号发送给管理员开通账户权限')


@billing_bp.route('/activation/info', methods=['GET'])
@optional_jwt
def get_activation_info():
    """返回知识星球开通方式说明"""
    return jsonify({
        'group_name': ZSXQ_GROUP_NAME,
        'join_url': ZSXQ_JOIN_URL,
        'qr_url': ZSXQ_QR_URL,
        'contact': ZSXQ_CONTACT,
        'instructions': [
            '通过下方链接或二维码加入知识星球',
            '加入成功后，将您的星球昵称/账号告知管理员',
            '管理员审核后，将在后台为您开通对应账户权限',
            '开通后即可在本站享受对应套餐功能'
        ]
    })


@billing_bp.route('/subscription/plans', methods=['GET'])
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
