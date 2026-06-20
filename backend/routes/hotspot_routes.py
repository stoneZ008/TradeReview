from flask import request, jsonify

from routes import hotspot_bp
from hotspot_fetcher import get_industry_sectors, get_concept_sectors, get_sector_stocks, clear_cache
from attribution_analyzer import analyze_stock_attribution, analyze_sector_attribution, get_market_overview


@hotspot_bp.route("/hotspot/sectors", methods=["GET"])
def get_sectors():
    limit = int(request.args.get("limit", 50))
    sector_type = request.args.get("type", "industry")
    if sector_type == "concept":
        sectors = get_concept_sectors(limit=limit)
    else:
        sectors = get_industry_sectors(limit=limit)

    return jsonify({"success": True, "data": sectors, "total": len(sectors)})


@hotspot_bp.route("/hotspot/sector/<sector_name>", methods=["GET"])
def get_sector_detail(sector_name):
    sector_type = request.args.get("type", "industry")
    stocks = get_sector_stocks(sector_name, sector_type)
    attribution = analyze_sector_attribution(sector_name, sector_type)

    return jsonify({"success": True, "stocks": stocks, "attribution": attribution})


@hotspot_bp.route("/hotspot/refresh", methods=["POST"])
def refresh_cache():
    try:
        cache_type = request.json.get("type") if request.is_json else None
        clear_cache(cache_type)
        return jsonify({"success": True, "message": "缓存已刷新"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@hotspot_bp.route("/hotspot/attribution/<code>", methods=["GET"])
def get_stock_attribution(code):
    name = request.args.get("name", "")
    result = analyze_stock_attribution(code, name)

    return jsonify({"success": True, "data": result})


@hotspot_bp.route("/hotspot/market-overview", methods=["GET"])
def get_market_overview_data():
    overview = get_market_overview()

    return jsonify({"success": True, "data": overview})
