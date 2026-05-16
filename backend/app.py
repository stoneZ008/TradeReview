from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
import os
from datetime import timedelta

from industry_db import seed_default_data
from user_db import seed_initial_data
from routes import auth_bp, stock_bp, admin_bp, watchlist_bp, industry_bp, billing_bp


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'trade-review-secret-key-2024')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

    JWTManager(app)
    Bcrypt(app)

    seed_default_data()
    seed_initial_data()

    app.register_blueprint(auth_bp)
    app.register_blueprint(stock_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(watchlist_bp)
    app.register_blueprint(industry_bp)
    app.register_blueprint(billing_bp)

    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok'})

    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=True, port=5000)
