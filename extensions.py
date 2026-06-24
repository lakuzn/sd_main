# Цетральное место всех расширений

import os
from dotenv import load_dotenv

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf_token = CSRFProtect()

# Загрузка переменных из .env
load_dotenv()

# Общая шина (Redis) для Socket.IO. Если REDIS_URL задан — состояние Socket.IO
# (комнаты, рассылки) хранится в Redis, и можно запускать НЕСКОЛЬКО воркеров
# gunicorn (-w >1) — без неё пришлось бы держать ровно один процесс.
_redis_url = os.environ.get("REDIS_URL") or None

socketio = SocketIO(
    cors_allowed_origins="*",
    # gevent: асинхронный режим — один воркер держит тысячи одновременных
    # соединений (вебсокеты/long-polling) без потока-на-соединение.
    async_mode="gevent",
    # При заданном REDIS_URL включаем горизонтальное масштабирование на N воркеров.
    message_queue=_redis_url,
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
