from flask import Blueprint

tickets_bp = Blueprint(
    "tickets",
    __name__,
    url_prefix="/tickets",
    template_folder="../templates/tickets",
    static_folder="../static",
)
