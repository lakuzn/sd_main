from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.blueprints.search import search_bp
from app.services.search_service import SearchService


@search_bp.route("/")
@login_required
def results():
    query_text = request.args.get("q", "").strip()

    tickets = []
    articles_by_category = {}

    if query_text:
        tickets = SearchService.search_tickets(query_text, current_user)
        articles_by_category = SearchService.search_articles_grouped_by_category(
            query_text
        )

    return render_template(
        "search/results.html",
        query_text=query_text,
        tickets=tickets,
        articles_by_category=articles_by_category,
    )
