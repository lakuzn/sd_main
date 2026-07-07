# Здесь мы будем собирать Flask и БД вместе

import logging
import sys

from flask import Flask, redirect, url_for, request, jsonify
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


def _setup_logging(app):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
    )
    app.logger.handlers = [handler]
    app.logger.setLevel(logging.INFO)
    # Werkzeug-логгер (на случай встроенного сервера) тоже в stdout
    logging.getLogger("werkzeug").addHandler(handler)


def _remote_user_for_log():
    header_user = request.headers.get("X-Remote-User")
    if header_user and header_user.strip() and header_user.strip() != "(null)":
        return header_user.strip()
    return (
        request.environ.get("REMOTE_USER")
        or request.environ.get("LOGON_USER")
        or "-"
    )


def _register_diagnostics(app):
    @app.after_request
    def _log_request(response):
        if request.path != "/healthz":
            app.logger.info(
                "%s %s -> %s | remote_user=%s | ip=%s",
                request.method,
                request.full_path.rstrip("?"),
                response.status_code,
                _remote_user_for_log(),
                request.remote_addr,
            )
        return response

    def _diag_page(code, title, hint):
        remote = _remote_user_for_log()
        body = (
            f"<!doctype html><html lang=ru><head><meta charset=utf-8>"
            f"<title>{code} {title}</title></head><body>"
            f"<h1>{code} {title}</h1>"
            f"<p>Этот ответ сформировало <b>приложение ServiceDesk (Flask/gunicorn)</b>, "
            f"а не Apache.</p>"
            f"<ul>"
            f"<li><b>Путь:</b> {request.method} {request.full_path.rstrip('?')}</li>"
            f"<li><b>Имя пользователя от Apache (X-Remote-User):</b> "
            f"{'(пусто — Kerberos/Basic не сработал)' if remote == '-' else remote}</li>"
            f"</ul>"
            f"<p>{hint}</p>"
            f"<p>Подробности — в журнале: <code>journalctl -u servicedesk -e</code> "
            f"и в <code>/var/log/httpd2/sd_error.log</code>.</p>"
            f"</body></html>"
        )
        if request.path.startswith("/api/"):
            return jsonify(error=title, code=code, path=request.full_path.rstrip("?")), code
        return body, code

    @app.errorhandler(404)
    def _not_found(e):
        app.logger.warning(
            "404 NOT FOUND: %s %s | remote_user=%s",
            request.method,
            request.full_path.rstrip("?"),
            _remote_user_for_log(),
        )
        return _diag_page(
            404,
            "Страница не найдена",
            "Такого маршрута в приложении нет. Проверьте URL и что gunicorn "
            "перезапущен после изменений кода (systemctl restart servicedesk), "
            "а в Apache ProxyPass указывает на http://127.0.0.1:8000/.",
        )

    @app.errorhandler(403)
    def _forbidden(e):
        app.logger.warning("403 FORBIDDEN: %s", request.full_path.rstrip("?"))
        return _diag_page(403, "Доступ запрещён", "Недостаточно прав для этой страницы.")

    @app.errorhandler(500)
    def _server_error(e):
        app.logger.exception("500 INTERNAL ERROR на %s", request.full_path.rstrip("?"))
        return _diag_page(
            500,
            "Внутренняя ошибка приложения",
            "Ошибка в коде приложения. Стек вызова записан в journalctl.",
        )

    @app.route("/healthz")
    def healthz():
        from app.extensions import db
        from sqlalchemy import text

        db_ok = True
        try:
            db.session.execute(text("SELECT 1"))
        except Exception as exc:
            db_ok = False
            app.logger.error("healthz: БД недоступна: %s", exc)
        return (
            jsonify(
                status="ok",
                app="servicedesk",
                db="ok" if db_ok else "error",
                remote_user=_remote_user_for_log(),
                kerberos_sso=app.config.get("KERBEROS_SSO_ENABLED"),
            ),
            200 if db_ok else 503,
        )

    @app.route("/whoami")
    def whoami():
        from flask_login import current_user

        header = request.headers.get("X-Remote-User")
        env_user = request.environ.get("REMOTE_USER") or request.environ.get("LOGON_USER")
        resolved = None
        raw = header if (header and header.strip() and header.strip() != "(null)") else env_user
        if raw:
            resolved = raw.split("\\")[-1].split("@")[0].strip().lower()
        return jsonify(
            header_x_remote_user=header,
            env_remote_user=env_user,
            resolved_username=resolved,
            authenticated=bool(current_user.is_authenticated),
            current_user=(
                getattr(current_user, "username", None)
                if current_user.is_authenticated
                else None
            ),
            kerberos_sso_enabled=app.config.get("KERBEROS_SSO_ENABLED"),
        )


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    _setup_logging(app)
    init_extensions(app)
    register_filters(app)
    _register_diagnostics(app)

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
