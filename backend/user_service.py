import sqlite3
from datetime import datetime, timedelta
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token
from user_db import get_connection
from auth import add_audit_log

def create_user(username, email, password):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
    if cursor.fetchone():
        conn.close()
        return None, '用户名或邮箱已存在'
    
    password_hash = generate_password_hash(password).decode('utf-8')
    trial_end = datetime.now() + timedelta(days=10)
    
    cursor.execute('''
        INSERT INTO users (username, email, password_hash, trial_end_at)
        VALUES (?, ?, ?, ?)
    ''', (username, email, password_hash, trial_end.isoformat()))
    
    user_id = cursor.lastrowid
    
    cursor.execute("SELECT id FROM roles WHERE name = 'user_free'")
    free_role = cursor.fetchone()
    if free_role:
        cursor.execute('INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)', (user_id, free_role[0]))
    
    conn.commit()
    conn.close()
    
    add_audit_log('register', 'user', user_id)
    return get_user_by_id(user_id), None

def authenticate_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, password_hash, is_active FROM users WHERE username = ? OR email = ?', (username, username))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return None, '用户名或密码错误'
    
    user_id, password_hash, is_active = row
    
    if not is_active:
        conn.close()
        return None, '账号已被禁用'
    
    if not check_password_hash(password_hash, password):
        conn.close()
        return None, '用户名或密码错误'
    
    cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', (datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()
    
    add_audit_log('login', 'auth', user_id)
    
    access_token = create_access_token(identity=str(user_id))
    refresh_token = create_refresh_token(identity=str(user_id))
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': get_user_by_id(user_id)
    }, None

def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, is_active, trial_end_at, last_login, created_at FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    user = dict(row)
    from auth import get_user_roles, get_user_subscription, is_trial_active
    user['roles'] = get_user_roles(user_id)
    user['subscription'] = get_user_subscription(user_id)
    user['is_trial_active'] = is_trial_active(user_id)
    return user

def get_user_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, username))
    row = cursor.fetchone()
    conn.close()
    if row:
        return get_user_by_id(row[0])
    return None

def change_password(user_id, old_password, new_password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT password_hash FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    
    if not check_password_hash(row['password_hash'], old_password):
        conn.close()
        return False, '原密码错误'
    
    new_hash = generate_password_hash(new_password).decode('utf-8')
    cursor.execute('UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?',
                  (new_hash, datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()
    
    add_audit_log('change_password', 'user', user_id)
    return True, None

def update_profile(user_id, username=None, email=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    updates = []
    params = []
    if username:
        cursor.execute('SELECT id FROM users WHERE username = ? AND id != ?', (username, user_id))
        if cursor.fetchone():
            conn.close()
            return None, '用户名已被使用'
        updates.append('username = ?')
        params.append(username)
    if email:
        cursor.execute('SELECT id FROM users WHERE email = ? AND id != ?', (email, user_id))
        if cursor.fetchone():
            conn.close()
            return None, '邮箱已被使用'
        updates.append('email = ?')
        params.append(email)
    
    if updates:
        updates.append('updated_at = ?')
        params.append(datetime.now().isoformat())
        params.append(user_id)
        
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
    
    conn.close()
    add_audit_log('update_profile', 'user', user_id)
    return get_user_by_id(user_id), None

def get_all_users(limit=100, offset=0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, username, email, is_active, trial_end_at, last_login, created_at
        FROM users ORDER BY id DESC LIMIT ? OFFSET ?
    ''', (limit, offset))
    rows = cursor.fetchall()
    conn.close()
    
    users = []
    for row in rows:
        user = dict(row)
        from auth import get_user_roles, get_user_subscription
        user['roles'] = get_user_roles(user['id'])
        user['subscription'] = get_user_subscription(user['id'])
        users.append(user)
    return users

def assign_user_role(user_id, role_name):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM roles WHERE name = ?", (role_name,))
    role = cursor.fetchone()
    if not role:
        conn.close()
        return False, '角色不存在'
    
    cursor.execute('DELETE FROM user_roles WHERE user_id = ?', (user_id,))
    cursor.execute('INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)', (user_id, role[0]))
    conn.commit()
    conn.close()
    
    add_audit_log(f'assign_role_{role_name}', 'admin', user_id)
    return True, None

def create_super_admin(username, email, password):
    user, err = create_user(username, email, password)
    if err:
        return None, err
    return assign_user_role(user['id'], 'super_admin')

def get_all_plans():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM subscription_plans ORDER BY id')
    rows = cursor.fetchall()
    conn.close()
    plans = []
    for row in rows:
        plan = dict(row)
        plan['features'] = __import__('json').loads(plan['features_json'])
        del plan['features_json']
        plans.append(plan)
    return plans

def assign_subscription(admin_user_id, target_user_id, plan_name, is_yearly=False):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM subscription_plans WHERE name = ?", (plan_name,))
    plan = cursor.fetchone()
    if not plan:
        conn.close()
        return False, '套餐不存在'
    
    plan_id = plan[0]
    start_date = datetime.now()
    duration = 365 if is_yearly else 30
    end_date = start_date + timedelta(days=duration)
    
    cursor.execute("UPDATE subscriptions SET status = 'expired' WHERE user_id = ?", (target_user_id,))
    
    cursor.execute('''
        INSERT INTO subscriptions (user_id, plan_id, start_date, end_date, status, created_by)
        VALUES (?, ?, ?, ?, 'active', ?)
    ''', (target_user_id, plan_id, start_date.isoformat(), end_date.isoformat(), admin_user_id))
    
    cursor.execute("SELECT id FROM roles WHERE name = ?", (f'user_{plan_name}',))
    role = cursor.fetchone()
    if role:
        cursor.execute('DELETE FROM user_roles WHERE user_id = ?', (target_user_id,))
        cursor.execute('INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)', (target_user_id, role[0]))
    
    conn.commit()
    conn.close()
    
    add_audit_log(f'assign_subscription_{plan_name}', 'admin', admin_user_id)
    return True, None
