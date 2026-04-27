import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'users.db')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, code)
        )
    ''')
    conn.commit()
    conn.close()


def get_watchlist(user_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT code, name FROM watchlist WHERE user_id = ? ORDER BY id', (user_id,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def add_to_watchlist(user_id, code, name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO watchlist (user_id, code, name) VALUES (?, ?, ?)',
                       (user_id, code, name))
        conn.commit()
        conn.close()
        return True, '添加成功'
    except sqlite3.IntegrityError:
        conn.close()
        return False, '该股票已在自选股中'
    except Exception as e:
        conn.close()
        return False, str(e)


def remove_from_watchlist(user_id, code):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM watchlist WHERE user_id = ? AND code = ?', (user_id, code))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    if deleted > 0:
        return True, '删除成功'
    return False, '股票不在自选股中'


init_db()
