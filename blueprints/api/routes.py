from flask import flash, render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.blueprints.api import api_bp
from app.services.dashboard_service import DashboardService
from app.services.ticket_service import TicketService
from app.services.notification_service import NotificationService
from app.models import Ticket, Notification, Category, User, Department
from app.extensions import socketio
from app.utils.decorators import role_required


# Поиск пользователей (для создания заявки от имени другого пользователя)
@api_bp.route("/users/search", methods=["GET"])
@login_required
@role_required(["classifier", "head", "executor", "admin"])
def search_users():
    query_str = request.args.get("q", "").strip()

    base_query = User.query
    if query_str:
        term = f"%{query_str}%"
        base_query = base_query.filter(
            or_(
                User.full_name.ilike(term),
                User.email.ilike(term),
            )
        )

    users = base_query.order_by(User.full_name).limit(10).all()

    return jsonify(
        [
            {
                "id": u.id,
                "full_name": u.full_name,
                "position": u.position or "—",
                "department": u.department.name if u.department else "Без отдела",
                "email": u.email,
            }
            for u in users
        ]
    )


# Опции фильтров дашборда (отделы и исполнители) с учётом роли
@api_bp.route("/dashboard/filter-options", methods=["GET"])
@login_required
@role_required(["classifier", "executor", "head", "admin"])
def dashboard_filter_options():
    from app.services.dashboard_service import DashboardService

    return jsonify(DashboardService.get_filter_options(current_user))


# API для фильтров
@api_bp.route("/filters/options", methods=["GET"])
@login_required
def get_filter_options():
    from app.models.category import Category

    categories = [c.name for c in Category.query.all()]

    return jsonify(
        {
            "categories": categories,
            "priorities": ["Высокий", "Средний", "Низкий"],
            "statuses": [
                "Новая",
                "В работе",
                "Ожидает ответа",
                "Требует проверки",
                "В обработке",
                "Решена",
            ],
        }
    )


# Отправка сообщения через socketio
@api_bp.route("/ticket/<int:ticket_id>/reply", methods=["POST"])
@login_required
def api_ticket_reply(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    # Проверка доступа к заявке
    if not TicketService.can_access_ticket(ticket, current_user):
        return (
            jsonify({"status": "error", "message": "У вас нет доступа к этой заявке"}),
            403,
        )

    content = request.form.get("content", "").strip()
    files = request.files.getlist("attachments")

    if not content and not (files and files[0].filename):
        return (
            jsonify(
                {"status": "error", "message": "Нельзя отправить пустое сообщение"}
            ),
            400,
        )

    if ticket.status == "Решена":
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Нельзя отправить сообщение в закрытую заявку",
                }
            ),
            400,
        )

    # Классификатор может писать в чат только пока заявка у него
    # (статус Новая/В обработке), ИЛИ если он также является исполнителем
    if current_user.role == "classifier":
        is_executor = current_user in ticket.executors
        if not is_executor and ticket.status not in ["Новая", "В обработке"]:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Классификатор не может писать в чат на данном этапе",
                    }
                ),
                403,
            )

    # Исполнитель пишет в чат только по своим заявкам (где он назначен) или по
    # собственному обращению. На заявки коллег по отделу — только просмотр.
    if (
        current_user.role == "executor"
        and current_user.id != ticket.applicant_id
        and current_user not in ticket.executors
    ):
        return (
            jsonify(
                {"status": "error", "message": "Вы не являетесь исполнителем этой заявки"}
            ),
            403,
        )

    TicketService.create_message(
        ticket_id=ticket_id,
        content=content,
        user=current_user,
        attachments=files,
    )

    return jsonify({"status": "success"})


# Смена статуса заявки
@api_bp.route("/ticket/<int:ticket_id>/status", methods=["POST"])
@login_required
@role_required(["user", "executor", "classifier", "admin", "head"])
def api_ticket_change_status(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    # Менять статус можно только у заявки, к которой есть доступ
    if not TicketService.can_access_ticket(ticket, current_user):
        return (
            jsonify({"status": "error", "message": "У вас нет доступа к этой заявке"}),
            403,
        )

    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    new_status = data.get("status")

    if not new_status:
        return jsonify({"error": "Status is required"}), 400

    allowed = [
        "Новая",
        "В работе",
        "Решена",
        "Ожидает ответа",
        "В обработке",
        "Требует проверки",
    ]
    if new_status not in allowed:
        return jsonify({"error": "Invalid status"}), 400

    old_status = ticket.status
    TicketService.change_status(ticket, new_status, current_user)

    # Уведомления только если статус действительно изменился
    if old_status != new_status:
        if new_status == "Решена":
            NotificationService.create_notification(
                user_id=ticket.applicant_id,
                message=f"Ваша заявка №{ticket.id} закрыта.",
                ticket_id=ticket.id,
            )
        elif new_status == "В обработке":
            NotificationService.create_notification(
                user_id=ticket.applicant_id,
                message=f"Ваша заявка №{ticket.id} в обработке.",
                ticket_id=ticket.id,
            )
        elif new_status == "В работе":
            NotificationService.create_notification(
                user_id=ticket.applicant_id,
                message=f"Ваша заявка №{ticket.id} передана в работу.",
                ticket_id=ticket.id,
            )
        elif new_status == "Ожидает ответа":
            NotificationService.create_notification(
                user_id=ticket.applicant_id,
                message=f"Исполнитель ожидает от Вас ответа по заявке №{ticket.id}.",
                ticket_id=ticket.id,
            )

    return jsonify({"status": "success", "new status": new_status})


# Создать похожую заявку (старая остаётся в архиве без изменений)
@api_bp.route("/ticket/<int:ticket_id>/clone", methods=["POST"])
@login_required
def api_clone_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    # Похожую заявку может создать сам заявитель, а также классификатор /
    # начальник / админ (например, из архива — с сохранением всех полей)
    if current_user.id != ticket.applicant_id and current_user.role not in [
        "classifier",
        "head",
        "admin",
    ]:
        return (
            jsonify(
                {"status": "error", "message": "У вас нет прав для этого действия"}
            ),
            403,
        )

    new_ticket = TicketService.clone_ticket(ticket_id, current_user)

    return jsonify(
        {
            "status": "success",
            "ticket_id": new_ticket.id,
        }
    )


# Мягкое удаление заявки (скрывается от пользователей, остаётся в БД)
@api_bp.route("/ticket/<int:ticket_id>/delete", methods=["POST"])
@login_required
def api_delete_ticket(ticket_id):
    success, result = TicketService.delete_ticket(ticket_id, current_user)

    if not success:
        return jsonify({"status": "error", "message": result}), 403

    return jsonify({"status": "success"})


@api_bp.route("/notifications", methods=["GET"])
@login_required
def get_notifications():
    notifications = NotificationService.get_unread_for_user(current_user.id)
    return jsonify([n.to_dict() for n in notifications])


@api_bp.route("/notifications/<int:notif_id>/read", methods=["POST"])
@login_required
def read_notification(notif_id):
    NotificationService.mark_as_read(notif_id, current_user.id)
    return jsonify({"success": True})


@api_bp.route("/notifications/read_all", methods=["POST"])
@login_required
def read_all_notifications():
    NotificationService.mark_all_as_read(current_user.id)
    return jsonify({"success": True})


# Отправка комментария через socketio
@api_bp.route("/ticket/<int:ticket_id>/internal_comment", methods=["POST"])
@login_required
@role_required(["executor", "classifier", "admin", "head"])
def api_comment_reply(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    # Проверка доступа
    if not TicketService.can_access_ticket(ticket, current_user):
        return (
            jsonify({"status": "error", "message": "У вас нет доступа к этой заявке"}),
            403,
        )

    comment_text = request.form.get("content", "").strip()
    files = request.files.getlist("attachments")

    if not comment_text and not (files and files[0].filename):
        return (
            jsonify(
                {"status": "error", "message": "Нельзя отправить пустой комментарий"}
            ),
            400,
        )

    # Классификатор может добавлять комментарии пока заявка у него
    # ИЛИ если он также является исполнителем
    if current_user.role == "classifier":
        is_executor = current_user in ticket.executors
        if not is_executor and ticket.status not in ["Новая", "В обработке"]:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Классификатор не может добавлять комментарии на данном этапе",
                    }
                ),
                403,
            )

    # Исполнитель оставляет внутренние комментарии только по своим заявкам
    if (
        current_user.role == "executor"
        and current_user.id != ticket.applicant_id
        and current_user not in ticket.executors
    ):
        return (
            jsonify(
                {"status": "error", "message": "Вы не являетесь исполнителем этой заявки"}
            ),
            403,
        )

    TicketService.create_comment(
        ticket_id=ticket_id,
        comment=comment_text,
        attachments=files,
    )

    return jsonify({"status": "success"})


@api_bp.route("/ticket/<int:ticket_id>/resolve", methods=["POST"])
@login_required
def api_resolve_ticket(ticket_id):

    success, result = TicketService.resolve_ticket(ticket_id, current_user)

    if not success:
        return jsonify({"status": "error", "message": result}), 403

    # Смена статуса уже разослана сокетом (ticket_status_changed) внутри resolve_ticket
    return jsonify({"status": "success"})


@api_bp.route("/ticket/<int:ticket_id>", methods=["PATCH"])
@login_required
@role_required(["classifier", "admin", "head", "executor"])
def change_ticket_params(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Классификатор может корректировать параметры заявки на любом этапе
    # (нельзя только в закрытой заявке)
    if ticket.status == "Решена":
        return (
            jsonify({"error": "Нельзя изменять параметры закрытой заявки"}),
            403,
        )

    # Исполнитель может менять только Host Name и номер документа
    # (например, когда машина не включается и host name заранее неизвестен)
    if current_user.role == "executor":
        if current_user not in ticket.executors:
            return (
                jsonify({"error": "Вы не являетесь исполнителем этой заявки"}),
                403,
            )
        allowed = {"host_name", "document_number"}
        data = {k: v for k, v in data.items() if k in allowed}
        if not data:
            return (
                jsonify({"error": "Недоступные для изменения поля"}),
                403,
            )

    TicketService.change_params(ticket, current_user, **data)

    return jsonify({"status": "success"})


# Параметры заявки
@api_bp.route("/ticket/params", methods=["GET"])
@login_required
@role_required(["classifier", "admin", "head", "executor"])
def get_ticket_params():
    categories = Category.query.all()
    categories_list = [{"id": c.id, "name": c.name} for c in categories]
    priorities = ["Высокий", "Средний", "Низкий"]
    statuses = [
        "Новая",
        "В работе",
        "Ожидает ответа",
        "В обработке",
        "Решена",
        "Требует проверки",
    ]

    executors = [
        {"id": u.id, "name": u.full_name}
        for u in User.query.filter_by(role="executor").all()
    ]

    departments = [{"id": d.id, "name": d.name} for d in Department.query.all()]

    return jsonify(
        {
            "categories": categories_list,
            "priorities": priorities,
            "statuses": statuses,
            "executors": executors,
            "departments": departments,
        }
    )


# Категории
@api_bp.route("/categories", methods=["GET"])
@login_required
def get_categories():
    categories = [{"id": c.id, "name": c.name} for c in Category.query.all()]

    return jsonify(
        {
            "categories": categories,
        }
    )

# API для фильтрации архива (возвращает JSON с HTML карточек и счётчиками)
@api_bp.route("/archive/tickets")
@login_required
def api_archive_tickets():
    """
    API эндпоинт для фильтрации архива.
    Принимает параметр type (my/executor/all).
    Возвращает JSON с HTML карточек и количеством заявок.
    """
    filter_type = request.args.get("type", "my")
    user_id = current_user.id
    role = current_user.role

    # Получаем данные через сервис
    result = DashboardService.get_archive_filtered_data(
        user_id=user_id,
        role=role,
        filter_type=filter_type
    )

    # Рендерим карточки в зависимости от типа фильтра
    my_html = ""
    executor_html = ""

    if filter_type == "my":
        my_html = render_template(
            "partials/pages/ticket/cards.html",
            tickets=result["my_tickets"],
            unread_ticket_ids=[],
            card_unclassified=False
        )
    elif filter_type == "executor":
        executor_html = render_template(
            "partials/pages/ticket/cards.html",
            tickets=result["executor_tickets"],
            unread_ticket_ids=[],
            card_unclassified=False
        )
    else:  # all
        if result["my_tickets"]:
            my_html = render_template(
                "partials/pages/ticket/cards.html",
                tickets=result["my_tickets"],
                unread_ticket_ids=[],
                card_unclassified=False
            )
        if result["executor_tickets"]:
            executor_html = render_template(
                "partials/pages/ticket/cards.html",
                tickets=result["executor_tickets"],
                unread_ticket_ids=[],
                card_unclassified=False
            )

    return {
        "my_html": my_html,
        "executor_html": executor_html,
        "count": result["total_count"],
        "counts": result["counts"]
    }