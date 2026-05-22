"""轻量级 SQLite schema 迁移工具

用法：
    from db_migrate import ensure_columns, run_migrations

    ensure_columns(conn, 'users', [
        ('phone', 'TEXT'),
        ('avatar_url', 'TEXT'),
    ])

或基于版本号的顺序迁移：
    run_migrations(conn, [
        ('001_add_phone', "ALTER TABLE users ADD COLUMN phone TEXT"),
        ('002_add_avatar', "ALTER TABLE users ADD COLUMN avatar_url TEXT"),
    ])

所有操作均为幂等，重复执行不会重复迁移。
"""

import sqlite3


def _table_exists(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def _existing_columns(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def ensure_columns(conn, table_name, columns):
    """确保表中存在指定列；不存在则 ALTER TABLE ADD COLUMN。

    columns: List[Tuple[str, str]]，例如 [('phone', 'TEXT'), ('age', 'INTEGER DEFAULT 0')]
    注意：SQLite 的 ALTER TABLE ADD COLUMN 有以下限制：
        - 不允许 PRIMARY KEY / UNIQUE 约束
        - 不允许默认值为 CURRENT_TIME/CURRENT_DATE/CURRENT_TIMESTAMP
        - NOT NULL 列必须带常量默认值
    本函数会自动剥离不兼容的子句以便兼容旧库的列补齐；遇到无法处理的会跳过并打印警告。
    """
    if not _table_exists(conn, table_name):
        return

    existing = _existing_columns(conn, table_name)
    cursor = conn.cursor()
    added = []
    for col_name, col_type in columns:
        if col_name in existing:
            continue
        safe_type = _sanitize_column_def(col_type)
        try:
            cursor.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {col_name} {safe_type}"
            )
            added.append(col_name)
        except sqlite3.OperationalError as e:
            print(f"[db_migrate] 警告: 跳过 {table_name}.{col_name} 迁移 ({e})")
    if added:
        conn.commit()
        print(f"[db_migrate] {table_name} 新增列: {', '.join(added)}")


def _sanitize_column_def(col_type):
    """剥离 ALTER TABLE ADD COLUMN 不支持的子句。"""
    upper = col_type.upper()
    cleaned = col_type
    # 去除 UNIQUE / PRIMARY KEY 约束
    for token in (' UNIQUE', ' PRIMARY KEY', ' AUTOINCREMENT'):
        idx = cleaned.upper().find(token)
        while idx != -1:
            cleaned = cleaned[:idx] + cleaned[idx + len(token):]
            idx = cleaned.upper().find(token)
    # CURRENT_TIMESTAMP 默认值改为 NULL
    if 'CURRENT_TIMESTAMP' in cleaned.upper():
        # 简化处理：直接去掉 DEFAULT CURRENT_TIMESTAMP
        import re
        cleaned = re.sub(
            r"DEFAULT\s+CURRENT_TIMESTAMP",
            '',
            cleaned,
            flags=re.IGNORECASE,
        )
    # NOT NULL 但没有默认值时，改为允许 NULL
    if 'NOT NULL' in cleaned.upper() and 'DEFAULT' not in cleaned.upper():
        cleaned = cleaned.replace('NOT NULL', '').replace('not null', '')
    return ' '.join(cleaned.split())


def _ensure_migrations_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id TEXT PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()


def run_migrations(conn, migrations):
    """按顺序执行未应用过的迁移。

    migrations: List[Tuple[migration_id, sql_or_callable]]
        - sql_or_callable 可以是 SQL 字符串，也可以是 callable(conn) -> None
    """
    _ensure_migrations_table(conn)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM schema_migrations')
    applied = {row[0] for row in cursor.fetchall()}

    for mig_id, action in migrations:
        if mig_id in applied:
            continue
        try:
            if callable(action):
                action(conn)
            else:
                cursor.execute(action)
            cursor.execute(
                'INSERT INTO schema_migrations (id) VALUES (?)', (mig_id,)
            )
            conn.commit()
            print(f"[db_migrate] 已应用迁移: {mig_id}")
        except sqlite3.OperationalError as e:
            # 列已存在等情况按已完成处理
            msg = str(e).lower()
            if 'duplicate column name' in msg or 'already exists' in msg:
                cursor.execute(
                    'INSERT OR IGNORE INTO schema_migrations (id) VALUES (?)',
                    (mig_id,)
                )
                conn.commit()
                print(f"[db_migrate] 跳过已存在的变更: {mig_id}")
            else:
                raise
