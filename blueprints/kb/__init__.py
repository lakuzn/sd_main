from flask import Blueprint

kb_bp = Blueprint(
    "kb",
    __name__,
    url_prefix="/kb",
    template_folder="../templates/kb",
    static_folder="../static",
)
