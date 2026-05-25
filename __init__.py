# Здесь мы будем собирать Flask и БД вместе

from flask import Flask, redirect, url_for
from flask_login import current_user, login_required
from app.extensions import init_extensions
from config import Config
from app.utils.filters import register_filters

from app.blueprints.tickets import socket_events
from app.blueprints.tickets.routes import tickets_bp
from app.blueprints.dashboards.routes import dashboards_bp
from app.blueprints.auth.routes import auth_bp
from app.blueprints.notifications.routes import notifications_bp
from app.blueprints.api.routes import api_bp
from app.blueprints.kb.routes import kb_bp
from app.blueprints.search.routes import search_bp
from app.blueprints.dashboards import dashboard_sockets


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    init_extensions(app)
    register_filters(app)

    app.register_blueprint(tickets_bp)
    app.register_blueprint(dashboards_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(kb_bp)
    app.register_blueprint(search_bp)

    @app.route("/")
    @login_required
    def home():
        """Главная страница - редирект по роли"""

        if current_user.role == "admin":
            return redirect(url_for("dashboards.admin"))
        elif current_user.role == "classifier":
            return redirect(url_for("dashboards.classifier"))
        elif current_user.role == "executor":
            return redirect(url_for("dashboards.executor"))
        elif current_user.role == "head":
            return redirect(url_for("dashboards.executor"))
        else:
            return redirect(url_for("dashboards.user"))

    @app.login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User

        return User.query.get(int(user_id))

    with app.app_context():
        from app import models

    return app


__all__ = ["create_app"]
