import sqlite3
import hashlib
import re
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'users.db')
SECRET_KEY = os.environ.get('SECRET_KEY', 'atrade-review-secret-key-2026')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    if len(password) < 6:
        return False, '密码长度至少6位'
    if password.isdigit():
        return False, '密码不能为纯数字'
    return True, ''


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(email, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (email, password_hash) VALUES (?, ?)',
                   (email, hash_password(password)))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id


def verify_user(email, password):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT id, email, password_hash, created_at FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    if user and user['password_hash'] == hash_password(password):
        return dict(user)
    return None


def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT id, email, created_at FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


def generate_token(user_id):
    import jwt
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def decode_token(token):
    import jwt
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload.get('user_id')
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


init_db()
