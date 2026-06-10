from flask_socketio import emit, join_room
from flask import request, session, url_for
from flask_login import login_required, current_user
from app.extensions import socketio
from app.services.ticket_service import TicketService
from app.models import Ticket, Message


@socketio.on("join_ticket")
def handle_join_ticket(data):
    ticket_id = data["ticket_id"]
    join_room(ticket_id)
    session["current_ticket"] = ticket_id


@socketio.on("join_user_room")
def handle_join_user_room():
    """Подписывает пользователя на его личную комнату уведомлений.

    Без этого уведомления (NotificationService шлёт их в комнату
    "user_<id>") не доходили бы в реальном времени — только после
    перезагрузки страницы.
    """
    if current_user.is_authenticated:
        join_room(f"user_{current_user.id}")
