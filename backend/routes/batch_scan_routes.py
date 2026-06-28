import time
import json
import os
from flask import request, jsonify, g
from routes import batch_scan_bp
from auth import requires_roles
from watchlist_scanner import _scan_single_stock

PRESET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'batch_scan_preset.json')


@batch_scan_bp.route("/preset", methods=["GET"])
@requires_roles("admin", "super_admin")
def get_batch_scan_preset():
    try:
        if os.path.exists(PRESET_FILE):
            with open(PRESET_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({"success": True, "content": content})
    except Exception:
        pass
    return jsonify({"success": True, "content": ""})


@batch_scan_bp.route("/preset", methods=["PUT"])
@requires_roles("admin", "super_admin")
def save_batch_scan_preset():
    data = request.json or {}
    content = data.get("content", "")
    try:
        with open(PRESET_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@batch_scan_bp.route("/scan", methods=["POST"])
@requires_roles("admin", "super_admin")
def batch_scan_signals():
    data = request.json or {}
    stocks = data.get("stocks", [])

    if not stocks or not isinstance(stocks, list):
        return jsonify({"success": False, "error": "stocks 参数不能为空"}), 400

    valid_stocks = []
    seen = set()
    for s in stocks:
        code = str(s.get("code", "")).strip()
        name = str(s.get("name", "")).strip()
        if not code or not code.isdigit() or not code[0] in ("0", "3", "6"):
            continue
        if code in seen:
            continue
        seen.add(code)
        valid_stocks.append({
            "code": code,
            "name": name,
            "industry": s.get("industry", ""),
            "sub_industry": s.get("sub_industry", ""),
        })

    if not valid_stocks:
        return jsonify({"success": False, "error": "没有有效的A股代码"}), 400

    results = []
    total = len(valid_stocks)
    for i, s in enumerate(valid_stocks):
        snap = _scan_single_stock(s["code"], s["name"])
        snap["industry"] = s["industry"]
        snap["sub_industry"] = s["sub_industry"]
        results.append(snap)
        if i < total - 1:
            time.sleep(0.5)

    return jsonify({"success": True, "data": results})
