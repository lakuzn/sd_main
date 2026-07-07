from gevent import monkey

monkey.patch_all()

try:
    from psycogreen.gevent import patch_psycopg

    patch_psycopg()
except Exception:  # пакет может быть не установлен
    pass


from app import create_app
from app.extensions import socketio

app = create_app()

if __name__ == "__main__":
    socketio.run(
        app,
        host="127.0.0.1",
        port=8000,
        debug=True,
        allow_unsafe_werkzeug=True,
    )

