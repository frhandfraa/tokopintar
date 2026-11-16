from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from app.config import Config

# Inisialisasi db dan jwt HARUS di luar fungsi create_app
db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Daftarkan db dan jwt ke aplikasi
    db.init_app(app)
    jwt.init_app(app)
    CORS(app)

    # Register blueprints (PENTING: Import di dalam fungsi agar tidak Circular Import)
    from app.auth import auth_bp
    from app.routes.products import products_bp
    from app.routes.interactions import interactions_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.views import views_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(products_bp, url_prefix="/api/products")
    app.register_blueprint(interactions_bp, url_prefix="/api/interactions")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(views_bp)  

    # TAMBAHAN: Halaman Error 404 Kustom
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    return app