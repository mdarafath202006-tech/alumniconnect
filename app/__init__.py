"""
app/__init__.py – Application factory.
Creates and configures the Flask app with all extensions.
"""
from flask import Flask
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import os

from config import config

# Extensions (initialised without app – use init_app pattern)
socketio = SocketIO(cors_allowed_origins="*")
limiter = Limiter(key_func=get_remote_address)
csrf = CSRFProtect()


def create_app(config_name: str = None):
    """
    Application factory.
    Usage:
        app = create_app()           # uses FLASK_ENV or 'default'
        app = create_app('production')
    """
    load_dotenv()  # load .env file

    config_name = config_name or os.environ.get("FLASK_ENV", "default")
    cfg = config.get(config_name, config["default"])

    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(cfg)

    # ── Bind extensions ──────────────────────────────────────────────────────
    socketio.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)

    # ── Register blueprints ──────────────────────────────────────────────────
    from app.auth.routes import auth_bp
    from app.routes.student import student_bp
    from app.routes.alumni import alumni_bp
    from app.routes.admin import admin_bp
    from app.routes.analytics import analytics_bp
    from app.api.routes import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp, url_prefix="/student")
    app.register_blueprint(alumni_bp, url_prefix="/alumni")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(analytics_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # ── Register SocketIO events ─────────────────────────────────────────────
    from app.services.chat import register_socket_events
    register_socket_events(socketio)

    # ── Root redirect ────────────────────────────────────────────────────────
    from flask import session, redirect, url_for, render_template

    @app.route("/")
    def index():
        if "user_id" in session:
            role = session.get("role")
            if role == "student":
                return redirect(url_for("student.dashboard"))
            if role == "alumni":
                return redirect(url_for("alumni.dashboard"))
            if role == "admin":
                return redirect(url_for("admin.dashboard"))
        return render_template("index.html")

    return app
