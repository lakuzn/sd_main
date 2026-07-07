from flask import flash, render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.blueprints.api import api_bp
from app.services.archive_service import ArchiveService
from app.services.dashboard_service import DashboardService
from app.services.ticket_service import TicketService
from app.services.notification_service import NotificationService
from app.models import Ticket, Notification, Category, User, Department
from app.extensions import socketio
from app.utils.decorators import role_required


@api_bp.route("/users/all", methods=["GET"])
@login_required
def get_all_users():
    query = User.query.filter_by(is_active=True)

    users = query.order_by(User.full_name).all()

    return jsonify(
        [
            {
                "id": u.id,
                "full_name": u.full_name,
                "position": u.position or "Сотрудник",
                "department": u.department.name if u.department else "Без отдела",
                "phone": u.phone or "Не указан",
                "email": u.email or "Не указан",
            }
            for u in users
        ]
    )


# Поиск пользователей для создания заявки от имени другого пользователя
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
                "position": u.position or "Сотрудник",
                "department": u.department.name if u.department else "Без отдела",
                "phone": u.phone or "Не указан",
                "email": u.email or "Не указан",
            }
            for u in users
        ]
    )


# Опции фильтров дашборда (отделы и исполнители)
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

    if (
        current_user.role == "executor"
        and current_user.id != ticket.applicant_id
        and current_user not in ticket.executors
    ):
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Вы не являетесь исполнителем этой заявки",
                }
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

    if old_status != new_status:
        if new_status == "Решена":
            NotificationService.create_notification(
                user_id=ticket.applicant_id,
                message=f"Ваша заявка №{ticket.id} закрыта.",
                ticket_id=ticket.id,
                important=True,
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


# Удаление заявки (остаётся в БД)
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


# Отправка комментария
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
                {
                    "status": "error",
                    "message": "Вы не являетесь исполнителем этой заявки",
                }
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

    if ticket.status == "Решена":
        return (
            jsonify({"error": "Нельзя изменять параметры закрытой заявки"}),
            403,
        )

    # Исполнитель может менять только Host Name и номер документа
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

    if current_user.role == "head" and "executor_ids" in data:
        allowed_ids = {
            u.id for u in TicketService.get_assignable_executors(current_user)
        }
        submitted_ids = [v for v in (data.get("executor_ids") or []) if isinstance(v, int)]
        if any(v not in allowed_ids for v in submitted_ids):
            return (
                jsonify(
                    {
                        "error": "Можно назначать только исполнителей своего отдела "
                        "и его подотделов"
                    }
                ),
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


# API для фильтрации архива
@api_bp.route("/archive/tickets")
@login_required
def api_archive_tickets():
    """API для получения архива заявок с фильтрацией"""
    filter_type = request.args.get("type", "all")

    data = ArchiveService.get_archive_data(
        current_user.id, current_user.role, filter_type
    )

    tickets_html = render_template(
        "partials/pages/archive/ticket_list.html", tickets=data["tickets"]
    )

    return jsonify(
        {
            "tickets_html": tickets_html,
            "counts": data["counts"],
            "current_filter": data["current_filter"],
        }
    )
