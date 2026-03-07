from flask import Flask, app
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
import os
# from app.routes.activity_routes import activity_bp
# app.register_blueprint(activity_bp)


# -------------------------------------------------
# Load environment variables from .env
# -------------------------------------------------
load_dotenv()

# -------------------------------------------------
# Extensions (initialized globally)
# -------------------------------------------------
db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_name='development'):
    """Application Factory"""

    app = Flask(__name__)

    # =================================================
    # BASIC CONFIGURATION
    # =================================================

    app.config['SECRET_KEY'] = os.getenv(
        'SECRET_KEY', 'dev-secret-key'
    )

    # PostgreSQL connection
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:password@localhost:5432/activity_db'
    )

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # =================================================
    # JWT CONFIGURATION
    # =================================================

    app.config['JWT_SECRET_KEY'] = os.getenv(
        'JWT_SECRET_KEY', 'jwt-secret-key'
    )

    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(
        os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600)
    )

    # =================================================
    # INITIALIZE EXTENSIONS
    # =================================================

    db.init_app(app)
    jwt.init_app(app)

    # Enable CORS for Flutter/mobile apps
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # =================================================
    # REGISTER BLUEPRINTS
    # =================================================

    from app.routes.auth_routes import auth_bp
    from app.routes.household_routes import household_bp
    from app.routes.access_routes import access_bp
    from app.routes.activity_routes import activity_bp
    from app.routes.device_routes import device_bp
    from app.routes.alert_routes import alert_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(household_bp, url_prefix="/api/household")
    app.register_blueprint(access_bp, url_prefix="/api/access")
    app.register_blueprint(activity_bp, url_prefix="/api/activity")
    app.register_blueprint(device_bp, url_prefix="/api/device")
    app.register_blueprint(alert_bp, url_prefix="/api/alert")
    # =================================================
    # HEALTH CHECK ENDPOINT
    # =================================================

    @app.route('/api/health', methods=['GET'])
    def health():
        return {
            "status": "ok",
            "message": "Backend is running"
        }, 200

    # =================================================
    # CREATE DATABASE TABLES (DEV ONLY)
    # =================================================
    # NOTE: In production use Flask-Migrate instead

    with app.app_context():
        db.create_all()

    return app
