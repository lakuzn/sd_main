# Главный скрипт (точка входа)
# ВАЖНО: gevent monkey_patch ДОЛЖЕН выполняться САМЫМ ПЕРВЫМ, до импорта Flask,
# SQLAlchemy и сети — иначе кооперативная многозадачность не заработает и под
# нагрузкой (100+ одновременных, Socket.IO) сервер будет «залипать».
from gevent import monkey

monkey.patch_all()

# Делаем psycopg2 (драйвер PostgreSQL) кооперативным с gevent,
# иначе любой запрос к БД блокировал бы весь воркер и все его соединения.
try:
    from psycogreen.gevent import patch_psycopg

    patch_psycopg()
except Exception:  # пакет может быть не установлен
    pass


from app import create_app
from app.extensions import socketio

app = create_app()

if __name__ == "__main__":
    # Запускаем встроенный сервер Flask для разработки
    # host='127.0.0.1' - это значит приложение развернуто только у нас на компах
    # host='0.0.0.0' - это значит, что сайт будет доступен не только для нас,
    # но и по локалке для других (по IP адресу)
    socketio.run(
        app,
        host="127.0.0.1",
        port=8000,
        debug=True,
        allow_unsafe_werkzeug=True,
    )

# ленин айпишник 172.31.4.134
