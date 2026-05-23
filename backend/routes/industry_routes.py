from flask import request, jsonify

from routes import industry_bp
from industry_db import (
    get_all_industries,
    add_industry,
    update_industry,
    add_sub_industry,
    update_sub_industry,
    add_company,
    update_company,
    delete_company,
)
from auth import requires_permission


@industry_bp.route("/industries", methods=["GET"])
@requires_permission("industry:read")
def get_industries():
    return jsonify({"data": get_all_industries()})


@industry_bp.route("/industries", methods=["POST"])
@requires_permission("industry:write")
def create_industry():
    data = request.json
    name = data.get("name", "")
    icon = data.get("icon", "🏢")
    if not name:
        return jsonify({"success": False, "error": "请输入行业名称"}), 400
    try:
        industry_id = add_industry(name, icon)
        return jsonify({"success": True, "id": industry_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@industry_bp.route("/industries/<int:industry_id>", methods=["PUT"])
@requires_permission("industry:write")
def edit_industry(industry_id):
    data = request.json
    name = data.get("name", "")
    icon = data.get("icon", "🏢")
    if not name:
        return jsonify({"success": False, "error": "请输入行业名称"}), 400
    try:
        update_industry(industry_id, name, icon)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@industry_bp.route("/sub-industries", methods=["POST"])
@requires_permission("industry:write")
def create_sub_industry():
    data = request.json
    industry_id = data.get("industry_id")
    name = data.get("name", "")
    if not industry_id or not name:
        return jsonify({"success": False, "error": "参数不完整"}), 400
    try:
        sub_id = add_sub_industry(industry_id, name)
        return jsonify({"success": True, "id": sub_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@industry_bp.route("/sub-industries/<int:sub_id>", methods=["PUT"])
@requires_permission("industry:write")
def edit_sub_industry(sub_id):
    data = request.json
    name = data.get("name", "")
    if not name:
        return jsonify({"success": False, "error": "请输入子行业名称"}), 400
    try:
        update_sub_industry(sub_id, name)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@industry_bp.route("/companies", methods=["POST"])
@requires_permission("industry:write")
def create_company():
    data = request.json
    sub_industry_id = data.get("sub_industry_id")
    code = data.get("code", "")
    name = data.get("name", "")
    role = data.get("role", "")
    feature = data.get("feature", "")
    description = data.get("description", "")
    if not sub_industry_id or not code or not name:
        return jsonify({"success": False, "error": "缺少公司代码或名称"}), 400
    try:
        company_id = add_company(sub_industry_id, code, name, role, feature, description)
        return jsonify({"success": True, "id": company_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@industry_bp.route("/companies/<int:company_id>", methods=["PUT"])
@requires_permission("industry:write")
def edit_company(company_id):
    data = request.json
    code = data.get("code", "")
    name = data.get("name", "")
    role = data.get("role", "")
    feature = data.get("feature", "")
    description = data.get("description", "")
    if not code or not name:
        return jsonify({"success": False, "error": "缺少公司代码或名称"}), 400
    try:
        update_company(company_id, code, name, role, feature, description)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@industry_bp.route("/companies/<int:company_id>", methods=["DELETE"])
@requires_permission("industry:write")
def remove_company(company_id):
    try:
        delete_company(company_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
