from flask import url_for

from app.extensions import db, socketio  # Если socketio настроен
from app.models.notification import Notification
from app.models.user import User


class NotificationService:

    @staticmethod
    def create_notification(user_id, message, ticket_id=None, important=False):
        notification = Notification(
            user_id=user_id, message=message, ticket_id=ticket_id
        )
        db.session.add(notification)

        db.session.commit()

        payload = notification.to_dict()
        payload["important"] = important
        socketio.emit(
            "new_notification",
            payload,
            room=f"user_{user_id}",
        )

        if important:
            NotificationService._send_email(user_id, message, ticket_id)

        return notification

    @staticmethod
    def _send_email(user_id, message, ticket_id):
        from app.services.email_service import EmailService

        if not EmailService.is_enabled():
            return

        user = User.query.get(user_id)
        if not user or not user.email:
            return

        ticket_url = None
        if ticket_id:
            try:
                ticket_url = url_for(
                    "tickets.view_ticket", ticket_id=ticket_id, _external=True
                )
            except Exception:
                ticket_url = None

        EmailService.send_notification_email(
            recipient=user.email,
            subject=f"ServiceDesk: {message}",
            message=message,
            ticket_url=ticket_url,
        )

    @staticmethod
    def notify_many(user_ids, message, ticket_id=None, important=False):
        for uid in {u for u in user_ids if u}:
            NotificationService.create_notification(uid, message, ticket_id, important)

    @staticmethod
    def get_unread_for_user(user_id):
        return (
            Notification.query.filter_by(user_id=user_id, is_read=False)
            .order_by(Notification.created_at.desc())
            .all()
        )

    @staticmethod
    def mark_as_read(notification_id, user_id):
        notification = Notification.query.filter_by(
            id=notification_id, user_id=user_id
        ).first()
        if notification:
            notification.is_read = True
            db.session.commit()
            return True
        return False

    @staticmethod
    def mark_all_as_read(user_id):
        Notification.query.filter_by(user_id=user_id, is_read=False).update(
            {"is_read": True}
        )
        db.session.commit()
