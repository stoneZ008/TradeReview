from flask import request, jsonify, g

from routes import admin_bp
from user_service import create_user, get_all_users, assign_user_role, assign_subscription
from user_db import get_connection
from auth import requires_roles


@admin_bp.route('/users', methods=['GET'])
@requires_roles('super_admin', 'admin')
def admin_list_users():
    users = get_all_users()
    return jsonify({'data': users})


@admin_bp.route('/users', methods=['POST'])
@requires_roles('super_admin', 'admin')
def admin_create_user():
    data = request.json
    username = data.get('username', '')
    email = data.get('email', '')
    password = data.get('password', '')
    
    if not username or not email or not password:
        return jsonify({'error': '请填写用户名、邮箱和密码'}), 400
    
    user, err = create_user(username, email, password)
    if err:
        return jsonify({'error': err}), 400
    return jsonify({'success': True, 'data': user})


@admin_bp.route('/users/<int:user_id>/subscription', methods=['PUT'])
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


@admin_bp.route('/users/<int:user_id>/roles', methods=['PUT'])
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


@admin_bp.route('/audit-logs', methods=['GET'])
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
