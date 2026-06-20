from flask import request, jsonify, g
import sqlite3

from routes import watchlist_bp
from user_db import get_connection
from auth import requires_permission
from watchlist_scanner import scan_user_watchlist, get_snapshots, has_today_snapshot


@watchlist_bp.route("", methods=["GET"])
@requires_permission("watchlist:read")
def get_watchlist():
    user_id = g.user_id if g.user_id else None

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT stock_code, stock_name FROM user_watchlists
        WHERE user_id = ? ORDER BY sort_order ASC, id ASC
    """,
        (user_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    watchlist = [{"code": row["stock_code"], "name": row["stock_name"]} for row in rows]
    return jsonify({"data": watchlist})


@watchlist_bp.route("", methods=["POST"])
@requires_permission("watchlist:write")
def add_watchlist():
    data = request.json
    code = data.get("code", "")
    name = data.get("name", "")
    user_id = g.user_id

    if not code or not name:
        return jsonify({"error": "缺少代码或名称"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO user_watchlists (user_id, stock_code, stock_name)
            VALUES (?, ?, ?)
        """,
            (user_id, code, name),
        )
        conn.commit()
        message = "添加成功"
    except sqlite3.IntegrityError:
        message = "该股票已在自选股中"
    conn.close()

    result = get_watchlist()
    response = result.get_json()
    response["success"] = True
    response["message"] = message
    return jsonify(response)


@watchlist_bp.route("/<code>", methods=["DELETE"])
@requires_permission("watchlist:write")
def delete_watchlist(code):
    user_id = g.user_id

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_watchlists WHERE user_id = ? AND stock_code = ?", (user_id, code))
    conn.commit()
    conn.close()

    result = get_watchlist()
    response = result.get_json()
    response["success"] = True
    response["message"] = "删除成功"
    return jsonify(response)


@watchlist_bp.route("/reorder", methods=["PUT"])
@requires_permission("watchlist:write")
def reorder_watchlist():
    """更新自选股排序。请求体: {"codes": ["600519", "000001", ...]}"""
    user_id = g.user_id
    data = request.json or {}
    codes = data.get("codes", [])
    if not isinstance(codes, list) or not codes:
        return jsonify({"error": "缺少 codes 列表"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    for idx, code in enumerate(codes):
        cursor.execute(
            "UPDATE user_watchlists SET sort_order = ? WHERE user_id = ? AND stock_code = ?",
            (idx, user_id, code),
        )
    conn.commit()
    conn.close()

    result = get_watchlist()
    response = result.get_json()
    response["success"] = True
    response["message"] = "排序成功"
    return jsonify(response)


@watchlist_bp.route("/signals", methods=["GET"])
@requires_permission("watchlist:read")
def get_watchlist_signals():
    """获取当日自选股信号快照。若当日无快照则即时扫描入库（懒加载兜底）。"""
    user_id = g.user_id
    if not user_id:
        return jsonify({"error": "需要登录"}), 401

    try:
        if not has_today_snapshot(user_id):
            snapshots, date_str = scan_user_watchlist(user_id, force=False)
        else:
            snapshots, date_str = get_snapshots(user_id)
        return jsonify({"success": True, "data": snapshots, "snapshot_date": date_str})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@watchlist_bp.route("/signals/refresh", methods=["POST"])
@requires_permission("watchlist:read")
def refresh_watchlist_signals():
    """强制重新扫描当日自选股信号，覆盖已有快照。"""
    user_id = g.user_id
    if not user_id:
        return jsonify({"error": "需要登录"}), 401

    try:
        snapshots, date_str = scan_user_watchlist(user_id, force=True)
        return jsonify({"success": True, "data": snapshots, "snapshot_date": date_str})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
