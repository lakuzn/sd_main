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

    if current_user.role in ["classifier", "admin", "head"]:
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
@role_required(["classifier", "admin", "head"])
def route_ticket(ticket_id):
    ticket = TicketService.get_ticket(ticket_id)

    if current_user.role == "classifier" and ticket.status not in ["Новая", "В обработке"]:
        flash("Маршрутизация доступна только для новых и необработанных заявок.", "warning")
        return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))

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
    ticket = TicketService.get_ticket(ticket_id)

    if current_user.role == "classifier" and ticket.status not in ["Новая", "В обработке"]:
        flash("Переназначение доступно только для новых и необработанных заявок.", "warning")
        return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))

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


# Взять заявку в работу (Исполнитель / Начальник отдела)
@tickets_bp.route("/ticket/<int:ticket_id>/take_in_work", methods=["POST"])
@login_required
@role_required(["executor", "head"])
def take_in_work(ticket_id):
    ticket = TicketService.get_ticket(ticket_id)
    result = TicketService.take_in_work(ticket, current_user)
    if result:
        flash("Вы взяли заявку в работу.", "success")
    else:
        flash(
            "Невозможно взять заявку в работу. "
            "Убедитесь, что заявка направлена в ваш отдел и ещё не имеет исполнителей.",
            "warning",
        )
    return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))


# Запросить проверку у заявителя (Исполнитель / Начальник отдела)
@tickets_bp.route("/ticket/<int:ticket_id>/request_review", methods=["POST"])
@login_required
@role_required(["executor", "head"])
def request_review(ticket_id):
    ticket = TicketService.get_ticket(ticket_id)
    if current_user not in ticket.executors:
        flash("Вы не являетесь исполнителем этой заявки.", "warning")
        return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))
    if ticket.status not in ["В работе", "Ожидает ответа"]:
        flash("Это действие недоступно при текущем статусе заявки.", "warning")
        return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))
    TicketService.request_review(ticket, current_user)
    flash("Запрос на проверку отправлен заявителю.", "success")
    return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))


# Заявка не решена — заявитель возвращает заявку в работу
@tickets_bp.route("/ticket/<int:ticket_id>/not_resolved", methods=["POST"])
@login_required
def not_resolved(ticket_id):
    ticket = TicketService.get_ticket(ticket_id)

    if current_user.id != ticket.applicant_id:
        flash("У вас нет прав для этого действия.", "danger")
        return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))

    if ticket.status != "Требует проверки":
        flash("Это действие доступно только когда заявка ожидает проверки.", "warning")
        return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))

    TicketService.reject_resolution(ticket, current_user)
    flash("Заявка возвращена в работу. Исполнители уведомлены.", "success")
    return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))


# Назначить заявку в отдел (Классификатор / Администратор)
@tickets_bp.route("/ticket/<int:ticket_id>/assign_department", methods=["POST"])
@login_required
@role_required(["classifier", "admin", "head"])
def assign_department(ticket_id):
    department_id = request.form.get("department_id", type=int)
    if not department_id:
        flash("Выберите отдел для назначения.", "warning")
        return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))

    ticket = TicketService.get_ticket(ticket_id)

    if current_user.role == "classifier" and ticket.status not in ["Новая", "В обработке"]:
        flash("Назначение отдела доступно только для новых и необработанных заявок.", "warning")
        return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))
    result = TicketService.assign_department(ticket, department_id, current_user)
    if result:
        flash("Заявка направлена в отдел.", "success")
    else:
        flash("Не удалось назначить отдел.", "danger")

    return redirect(url_for("tickets.view_ticket", ticket_id=ticket_id))
