from flask import flash, request, jsonify
from flask_login import login_required, current_user
from app.blueprints.api import api_bp
from app.services.ticket_service import TicketService
from app.services.notification_service import NotificationService
from app.models import Ticket, Notification, Category, User
from app.extensions import socketio
from app.utils.decorators import role_required


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
                "Требуется проверка" "В обработке",
                "Решена",
            ],
        }
    )


# Отправка сообщения через socketio
@api_bp.route("/ticket/<int:ticket_id>/reply", methods=["POST"])
@login_required
def api_ticket_reply(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    content = request.form.get("content", "").strip()
    files = request.files.getlist("attachments")  # Ловим файлы из формы

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

    if current_user.role == "executor":
        executor_ids = [ex.id for ex in ticket.executors]
        if current_user.id not in executor_ids:
            return (
                jsonify(
                    {"status": "error", "message": "У вас нет доступа к этой заявке"}
                ),
                403,
            )

    if current_user.role == "classifier" and ticket.status not in [
        "Новая",
        "В обработке",
    ]:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Классификатор не может писать в чат на данном этапе",
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
        "Требуется проверка",
    ]
    if new_status not in allowed:
        return jsonify({"error": "Invalid status"}), 400

    TicketService.change_status(ticket, new_status, current_user)

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
    flash("Заявка отмечена как решенная", "success")
    return jsonify({"status": "success", "new status": new_status})


@api_bp.route("/notifications", methods=["GET"])
@login_required
def get_notifications():
    notifications = NotificationService.get_unread_for_user(current_user.id)
    return jsonify([n.to_dict() for n in notifications])


@api_bp.route("/notifications/<int:notif_id>/read", methods=["POST"])
@login_required
def read_notifications(notif_id):
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

    comment = request.form.get("content", "").strip()

    if not comment:
        return (
            jsonify(
                {"status": "error", "comment": "Нельзя отправить пустой комментарий"}
            ),
            400,
        )

    if current_user.role == "executor":
        executor_ids = [ex.id for ex in ticket.executors]
        if current_user.id not in executor_ids:
            return (
                jsonify(
                    {"status": "error", "message": "У вас нет доступа к этой заявке"}
                ),
                403,
            )

    if current_user.role == "classifier" and ticket.status not in [
        "Новая",
        "В обработке",
    ]:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Классификатор не может добавлять комментарии на данном этапе",
                }
            ),
            403,
        )

    TicketService.create_comment(
        ticket_id=ticket_id,
        comment=comment,
    )

    return jsonify({"status": "success"})


@api_bp.route("/ticket/<int:ticket_id>/resolve", methods=["POST"])
@login_required
def api_resolve_ticket(ticket_id):

    success, result = TicketService.resolve_ticket(ticket_id, current_user)

    if not success:
        return jsonify({"status": "error", "message": result}), 403

    socketio.emit("ticket_resolved", {"new_status": "Решена"}, room=str(ticket_id))

    return jsonify({"status": "success"})


@api_bp.route("/ticket/<int:ticket_id>", methods=["PATCH"])
@login_required
@role_required(["classifier", "admin", "head"])
def change_ticket_params(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    if current_user.role == "classifier" and ticket.status not in [
        "Новая",
        "В обработке",
    ]:
        return (
            jsonify({"error": "Нельзя изменять параметры заявки в данном статусе"}),
            403,
        )

    TicketService.change_params(ticket, current_user, **data)

    return jsonify({"status": "success"})


# Параметры заявки
# Убрать "user"
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
        "Требуется проверка",
    ]

    executors = [
        {"id": u.id, "name": u.full_name}
        for u in User.query.filter_by(role="executor").all()
    ]

    return jsonify(
        {
            "categories": categories_list,
            "priorities": priorities,
            "statuses": statuses,
            "executors": executors,
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
