from flask import Flask, app, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from app.config import Config
from datetime import timedelta


db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

    db.init_app(app)
    jwt.init_app(app)
    CORS(app)

    # Register blueprints (Semua sekarang ada di folder routes)
    from app.routes.auth import auth_bp       # Lokasi baru
    from app.routes.products import products_bp
    from app.routes.interactions import interactions_bp
    from app.routes.admin import admin_bp     # Dashboard Admin
    from app.routes.views import views_bp
    from app.routes.orders import orders_bp
    from app.routes.profile import profile_bp

    app.register_blueprint(profile_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(products_bp, url_prefix="/api/products")
    app.register_blueprint(interactions_bp, url_prefix="/api/interactions")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(views_bp)  

    # Halaman Error 404 Kustom
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    return app