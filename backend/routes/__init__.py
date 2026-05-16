from flask import Blueprint

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
stock_bp = Blueprint('stock', __name__, url_prefix='/api')
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')
watchlist_bp = Blueprint('watchlist', __name__, url_prefix='/api/watchlist')
industry_bp = Blueprint('industry', __name__, url_prefix='/api')
billing_bp = Blueprint('billing', __name__, url_prefix='/api')

from . import auth_routes, stock_routes, admin_routes, watchlist_routes, industry_routes, billing_routes
