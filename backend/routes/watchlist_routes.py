from flask import request, jsonify, g
import sqlite3

from routes import watchlist_bp
from user_db import get_connection
from auth import requires_permission


@watchlist_bp.route('', methods=['GET'])
@requires_permission('watchlist:read')
def get_watchlist():
    user_id = g.user_id if g.user_id else None
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT stock_code, stock_name FROM user_watchlists
        WHERE user_id = ? ORDER BY created_at DESC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    watchlist = [{'code': row['stock_code'], 'name': row['stock_name']} for row in rows]
    return jsonify({'data': watchlist})


@watchlist_bp.route('', methods=['POST'])
@requires_permission('watchlist:write')
def add_watchlist():
    data = request.json
    code = data.get('code', '')
    name = data.get('name', '')
    user_id = g.user_id
    
    if not code or not name:
        return jsonify({'error': '缺少代码或名称'}), 400
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO user_watchlists (user_id, stock_code, stock_name)
            VALUES (?, ?, ?)
        ''', (user_id, code, name))
        conn.commit()
        message = '添加成功'
    except sqlite3.IntegrityError:
        message = '该股票已在自选股中'
    conn.close()
    
    result = get_watchlist()
    response = result.get_json()
    response['success'] = True
    response['message'] = message
    return jsonify(response)


@watchlist_bp.route('/<code>', methods=['DELETE'])
@requires_permission('watchlist:write')
def delete_watchlist(code):
    user_id = g.user_id
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_watchlists WHERE user_id = ? AND stock_code = ?', (user_id, code))
    conn.commit()
    conn.close()
    
    result = get_watchlist()
    response = result.get_json()
    response['success'] = True
    response['message'] = '删除成功'
    return jsonify(response)
