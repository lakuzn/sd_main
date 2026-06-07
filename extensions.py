# Цетральное место всех расширений

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf_token = CSRFProtect()

socketio = SocketIO(
    cors_allowed_origins="*",
)


def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf_token.init_app(app)
    socketio.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Пожалуйста, авторизуйтесь для доступа к системе."
    login_manager.login_message_category = "info"
