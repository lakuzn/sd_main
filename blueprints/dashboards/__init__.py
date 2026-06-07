from flask import Blueprint

dashboards_bp = Blueprint(
    "dashboards",
    __name__,
    url_prefix="/",
    template_folder="../templates/dashboards",
)
