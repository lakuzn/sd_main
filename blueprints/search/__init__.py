from flask import Blueprint

search_bp = Blueprint(
    "search",
    __name__,
    url_prefix="/search",
    template_folder="../templates/search",
)
