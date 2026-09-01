"""个股策略配置存储层"""

import json
from user_db import get_connection


def get_stock_strategies(user_id, stock_code):
    """获取用户某只股票的所有策略配置"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, stock_code, stock_name, config_name, config_json, is_default, "
        "created_at, updated_at FROM user_stock_strategies "
        "WHERE user_id = ? AND stock_code = ? ORDER BY is_default DESC, updated_at DESC",
        (user_id, stock_code),
    )
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        try:
            config = json.loads(row["config_json"])
        except (json.JSONDecodeError, TypeError):
            config = {}
        result.append(
            {
                "id": row["id"],
                "stock_code": row["stock_code"],
                "stock_name": row["stock_name"],
                "config_name": row["config_name"],
                "config": config,
                "is_default": bool(row["is_default"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        )
    return result


def get_default_strategy(user_id, stock_code):
    """获取用户某只股票的默认策略配置"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, config_name, config_json, stock_name FROM user_stock_strategies "
        "WHERE user_id = ? AND stock_code = ? AND is_default = 1 LIMIT 1",
        (user_id, stock_code),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    try:
        config = json.loads(row["config_json"])
    except (json.JSONDecodeError, TypeError):
        config = {}
    return {
        "id": row["id"],
        "config_name": row["config_name"],
        "config": config,
        "stock_name": row["stock_name"],
    }


def save_stock_strategy(user_id, stock_code, stock_name, config_name, config, is_default=False):
    """保存或更新策略配置（upsert）"""
    conn = get_connection()
    cursor = conn.cursor()

    config_json = json.dumps(config, ensure_ascii=False)

    if is_default:
        cursor.execute(
            "UPDATE user_stock_strategies SET is_default = 0 "
            "WHERE user_id = ? AND stock_code = ?",
            (user_id, stock_code),
        )

    cursor.execute(
        "SELECT id FROM user_stock_strategies "
        "WHERE user_id = ? AND stock_code = ? AND config_name = ?",
        (user_id, stock_code, config_name),
    )
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            "UPDATE user_stock_strategies SET stock_name = ?, config_json = ?, "
            "is_default = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (stock_name, config_json, 1 if is_default else 0, existing["id"]),
        )
        strategy_id = existing["id"]
    else:
        cursor.execute(
            "INSERT INTO user_stock_strategies "
            "(user_id, stock_code, stock_name, config_name, config_json, is_default) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, stock_code, stock_name, config_name, config_json, 1 if is_default else 0),
        )
        strategy_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return strategy_id


def delete_stock_strategy(user_id, stock_code, config_name):
    """删除策略配置"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM user_stock_strategies "
        "WHERE user_id = ? AND stock_code = ? AND config_name = ?",
        (user_id, stock_code, config_name),
    )
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    return deleted > 0
