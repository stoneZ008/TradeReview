from flask import request, jsonify, g
from flask_jwt_extended import create_access_token

from routes import auth_bp
from user_service import create_user, authenticate_user, get_user_by_id, change_password, update_profile
from auth import jwt_required, check_backtest_quota


@auth_bp.route('/register', methods=['POST'])
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


@auth_bp.route('/login', methods=['POST'])
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


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required
def refresh():
    new_token = create_access_token(identity=str(g.user_id))
    return jsonify({'access_token': new_token})


@auth_bp.route('/profile', methods=['GET'])
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


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required
def put_profile():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    
    user, err = update_profile(g.user_id, username, email)
    if err:
        return jsonify({'error': err}), 400
    return jsonify(user)


@auth_bp.route('/change-password', methods=['POST'])
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
