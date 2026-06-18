# Главный скрипт (точка входа)
from app import create_app
from app.extensions import socketio

# Собираем наше приложение
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

# мой айпишник 172.31.4.134
