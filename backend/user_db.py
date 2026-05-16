import sqlite3
import json
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'users.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_user_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            trial_end_at TIMESTAMP,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            is_system INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            resource TEXT NOT NULL,
            action TEXT NOT NULL,
            description TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS role_permissions (
            role_id INTEGER NOT NULL,
            permission_id INTEGER NOT NULL,
            PRIMARY KEY (role_id, permission_id),
            FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
            FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_roles (
            user_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, role_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscription_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            monthly_price REAL NOT NULL DEFAULT 0,
            yearly_price REAL NOT NULL DEFAULT 0,
            max_backtests_monthly INTEGER DEFAULT -1,
            features_json TEXT DEFAULT '{}',
            description TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan_id INTEGER NOT NULL,
            start_date TIMESTAMP NOT NULL,
            end_date TIMESTAMP NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (plan_id) REFERENCES subscription_plans(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS backtest_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            count INTEGER DEFAULT 0,
            month TEXT NOT NULL,
            UNIQUE(user_id, month),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_watchlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            stock_code TEXT NOT NULL,
            stock_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, stock_code),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            resource TEXT,
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def seed_initial_data():
    import os
    init_user_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM roles')
    roles_exist = cursor.fetchone()[0] > 0
    
    cursor.execute('SELECT COUNT(*) FROM users')
    users_exist = cursor.fetchone()[0] > 0
    
    if roles_exist and users_exist:
        conn.close()
        return
    
    roles = [
        ('super_admin', '超级管理员', 1),
        ('admin', '管理员', 1),
        ('user_pro', '专业版用户', 1),
        ('user_basic', '基础版用户', 1),
        ('user_free', '免费用户', 1),
        ('guest', '访客', 1)
    ]
    for name, desc, is_system in roles:
        cursor.execute('INSERT INTO roles (name, description, is_system) VALUES (?, ?, ?)', (name, desc, is_system))
    
    permissions = [
        ('stock:read', 'stock', 'read', '查看股票数据'),
        ('stock:write', 'stock', 'write', '管理股票数据'),
        ('backtest:run', 'backtest', 'run', '运行回测'),
        ('watchlist:read', 'watchlist', 'read', '查看自选股'),
        ('watchlist:write', 'watchlist', 'write', '管理自选股'),
        ('industry:read', 'industry', 'read', '查看行业数据'),
        ('industry:write', 'industry', 'write', '管理行业数据'),
        ('admin:users', 'admin', 'users', '管理用户'),
        ('admin:roles', 'admin', 'roles', '管理角色权限'),
        ('admin:subscriptions', 'admin', 'subscriptions', '管理订阅'),
        ('profile:read', 'profile', 'read', '查看个人资料'),
        ('profile:write', 'profile', 'write', '修改个人资料')
    ]
    for name, resource, action, desc in permissions:
        cursor.execute('INSERT INTO permissions (name, resource, action, description) VALUES (?, ?, ?, ?)',
                      (name, resource, action, desc))
    
    cursor.execute('SELECT id, name FROM roles')
    role_map = {name: id for id, name in cursor.fetchall()}
    
    cursor.execute('SELECT id, name FROM permissions')
    perm_map = {name: id for id, name in cursor.fetchall()}
    
    super_admin_perms = list(perm_map.values())
    for perm_id in super_admin_perms:
        cursor.execute('INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)',
                      (role_map['super_admin'], perm_id))
    
    admin_perms = [
        'stock:read', 'stock:write', 'backtest:run',
        'watchlist:read', 'watchlist:write', 'industry:read', 'industry:write',
        'admin:users', 'admin:subscriptions', 'profile:read', 'profile:write'
    ]
    for perm_name in admin_perms:
        cursor.execute('INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)',
                      (role_map['admin'], perm_map[perm_name]))
    
    user_pro_perms = [
        'stock:read', 'backtest:run', 'watchlist:read', 'watchlist:write',
        'industry:read', 'profile:read', 'profile:write'
    ]
    for perm_name in user_pro_perms:
        cursor.execute('INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)',
                      (role_map['user_pro'], perm_map[perm_name]))
    
    user_basic_perms = [
        'stock:read', 'backtest:run', 'watchlist:read', 'watchlist:write',
        'industry:read', 'profile:read', 'profile:write'
    ]
    for perm_name in user_basic_perms:
        cursor.execute('INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)',
                      (role_map['user_basic'], perm_map[perm_name]))
    
    user_free_perms = [
        'stock:read', 'watchlist:read', 'watchlist:write', 'profile:read', 'profile:write'
    ]
    for perm_name in user_free_perms:
        cursor.execute('INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)',
                      (role_map['user_free'], perm_map[perm_name]))
    
    guest_perms = []
    for perm_name in guest_perms:
        cursor.execute('INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)',
                      (role_map['guest'], perm_map[perm_name]))
    
    plans = [
        ('trial', 0, 0, 10, json.dumps({'indicators': True, 'dao_page': True}), '新用户注册自动获得 10 天试用'),
        ('basic', 0, 0, 20, json.dumps({'indicators': True, 'dao_page': False}), '基础版（知识星球开通）'),
        ('pro', 0, 0, 100, json.dumps({'indicators': True, 'dao_page': True}), '专业版（知识星球开通）'),
        ('enterprise', 0, 0, -1, json.dumps({'indicators': True, 'dao_page': True, 'priority_support': True}), '企业版（知识星球开通）')
    ]
    for name, monthly_price, yearly_price, max_backtests, features, desc in plans:
        cursor.execute('''
            INSERT INTO subscription_plans (name, monthly_price, yearly_price, max_backtests_monthly, features_json, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, monthly_price, yearly_price, max_backtests, features, desc))
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE id = 1')
    if cursor.fetchone()[0] == 0:
        from flask_bcrypt import generate_password_hash
        from datetime import datetime, timedelta
        
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@tradereview.local')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        password_hash = generate_password_hash(admin_password).decode('utf-8')
        trial_end = (datetime.now() + timedelta(days=365*10)).isoformat()
        
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, trial_end_at, is_active)
            VALUES (?, ?, ?, ?, 1)
        ''', (admin_username, admin_email, password_hash, trial_end))
        
        admin_id = cursor.lastrowid
        
        cursor.execute('SELECT id FROM roles WHERE name = ?', ('super_admin',))
        super_admin_role_id = cursor.fetchone()[0]
        
        cursor.execute('''
            INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)
        ''', (admin_id, super_admin_role_id))
        
        cursor.execute('SELECT id FROM subscription_plans WHERE name = ?', ('enterprise',))
        enterprise_plan_id = cursor.fetchone()[0]
        
        start_date = datetime.now().isoformat()
        end_date = (datetime.now() + timedelta(days=365*10)).isoformat()
        
        cursor.execute('''
            INSERT INTO subscriptions (user_id, plan_id, start_date, end_date, status, assigned_by)
            VALUES (?, ?, ?, ?, 'active', 0)
        ''', (admin_id, enterprise_plan_id, start_date, end_date))
        
        print(f'默认管理员账号已创建: {admin_username} / {admin_email}')
    
    conn.commit()
    conn.close()
    print('用户系统初始化完成')

if __name__ == '__main__':
    seed_initial_data()
