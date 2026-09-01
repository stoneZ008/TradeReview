from flask import Blueprint

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
stock_bp = Blueprint("stock", __name__, url_prefix="/api")
admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")
watchlist_bp = Blueprint("watchlist", __name__, url_prefix="/api/watchlist")
industry_bp = Blueprint("industry", __name__, url_prefix="/api")
billing_bp = Blueprint("billing", __name__, url_prefix="/api")
hotspot_bp = Blueprint("hotspot", __name__, url_prefix="/api")
experimental_bp = Blueprint("experimental", __name__, url_prefix="/api/experimental")
batch_scan_bp = Blueprint("batch_scan", __name__, url_prefix="/api/batch-scan")
strategy_bp = Blueprint("strategy", __name__, url_prefix="/api/strategy")

from . import (  # noqa: E402,F401
    auth_routes,
    stock_routes,
    admin_routes,
    watchlist_routes,
    industry_routes,
    billing_routes,
    hotspot_routes,
    experimental_routes,
    batch_scan_routes,
    strategy_routes,
)
