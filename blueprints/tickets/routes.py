from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.blueprints.tickets import tickets_bp
from app.forms.ticket_forms import *
from app.services.ticket_service import TicketService
from app.utils.decorators import role_required
from app.utils.forms import flash_form_errors


# Создание новой заявки
@tickets_bp.route("/new_ticket", methods=["GET", "POST"])
@login_required
def new_ticket():
    form = TicketForm()

    if form.validate_on_submit():
        TicketService.create_ticket(
            applicant_id=current_user.id,
            description=form.description.data.strip(),
            attachments=request.files.getlist("attachments"),
            desired_deadline=form.desired_deadline.data,
        )

        flash("Заявка успешно создана.", "success")
        return redirect(url_for("dashboards.user"))

    return render_template(
        "tickets/new_ticket.html",
        form=form,
    )


# Просмотр конкретной заявки
@tickets_bp.route("/<int:ticket_id>", methods=["GET"])
@login_required
def view_ticket(ticket_id):
    form = None

    if current_user.role in ["classifier", "admin"]:
        form = RouteTicketForm()
        TicketService.setup_route_form(form)

    context = TicketService.get_ticket_context(ticket_id, current_user, form)

    reassign_form = ReassignTicketForm()
    TicketService.setup_executor_choices(reassign_form)
    reassign_form.executor_ids.data = [ex.id for ex in context["ticket"].executors]

    context["reassign_form"] = reassign_form

    return render_template(
        "tickets/ticket.html",
        **context,
    )


# Маршрутизация заявки (Классификатор)
@tickets_bp.route("/ticket/<int:ticket_id>/route", methods=["POST"])
@login_required
@role_required(["classifier", "admin"])
def route_ticket(ticket_id):
    form = RouteTicketForm()

    # Заполняем для валидации
    TicketService.setup_route_form(form)

    if form.validate_on_submit():
        TicketService.route_ticket_action(ticket_id, form, current_user)
        flash("Заявка успешно маршрутизирована", "success")
    else:
        flash_form_errors(form)

    return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))


@tickets_bp.route("/ticket/<int:ticket_id>/reassign", methods=["POST"])
@login_required
@role_required(["classifier", "admin", "head"])
def reassign_ticket(ticket_id):
    form = ReassignTicketForm()
    TicketService.setup_executor_choices(form)

    if form.validate_on_submit():
        TicketService.reassign_ticket(
            ticket_id=ticket_id,
            executor_ids=form.executor_ids.data,
            user=current_user,
        )
        flash("Исполнители успешно обновлены.", "success")
    else:
        flash_form_errors(form)

    return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))


@tickets_bp.route("/card/<int:ticket_id>")
@login_required
def get_ticket_card(ticket_id):
    ticket = TicketService.get_ticket(ticket_id)

    if current_user.role == "user":
        template = "partials/pages/ticket/card.html"
    else:
        template = "partials/pages/ticket/card_unclassified.html"

    html = render_template(template, ticket=ticket)

    return {
        "html": html,
        "ticket_id": ticket.id,
    }
