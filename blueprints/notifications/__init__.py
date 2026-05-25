from flask import Blueprint

notifications_bp = Blueprint(
    "notifications",
    __name__,
    static_folder="../static",
)
