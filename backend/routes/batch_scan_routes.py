import time
from flask import request, jsonify, g
from routes import batch_scan_bp
from auth import requires_roles
from watchlist_scanner import _scan_single_stock


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
