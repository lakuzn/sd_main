from datetime import datetime
from flask import Flask


def register_filters(app: Flask):
    @app.template_filter("is_past")
    def is_past(date):
        return date < datetime.now()
