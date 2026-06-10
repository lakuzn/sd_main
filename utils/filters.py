from datetime import datetime
from flask import Flask


def register_filters(app: Flask):
    @app.template_filter("is_past")
    def is_past(date):
        # Заявка просрочена только после 23:59 дня дедлайна,
        # то есть если дата дедлайна строго меньше сегодняшней даты
        return date.date() < datetime.now().date()
