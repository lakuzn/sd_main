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


@search_bp.route("/filter")
@login_required
def filter():
    query_text = request.args.get("q", "").strip()
    content_type = request.args.get("type", "all")

    tickets = []
    articles_by_category = {}
    tickets_count = 0
    articles_count = 0

    if query_text:
        tickets, tickets_count = SearchService.search_tickets(query_text, current_user)
        articles_by_category, articles_count = (
            SearchService.search_articles_grouped_by_category(query_text)
        )

    html_tickets = ""
    html_knowledge = ""

    if content_type in ("all", "tickets") and tickets:
        html_tickets = render_template(
            "partials/pages/search/tickets.html",
            tickets=tickets,
        )
    if content_type in ("all", "knowledge") and articles_by_category:
        html_knowledge = render_template(
            "partials/pages/search/knowledge.html",
            articles_by_category=articles_by_category,
        )

    return {
        "html_tickets": html_tickets,
        "html_knowledge": html_knowledge,
        "counts": {
            "all": tickets_count + articles_count,
            "tickets": tickets_count,
            "knowledge": articles_count,
        },
    }
