from app.extensions import db, socketio  # Если socketio настроен
from app.models.notification import Notification


class NotificationService:

    @staticmethod
    def create_notification(user_id, message, ticket_id=None):
        """Создает уведомление в БД и сразу отправляет его через веб-сокеты"""
        notification = Notification(
            user_id=user_id, message=message, ticket_id=ticket_id
        )
        db.session.add(notification)

        db.session.commit()

        # Если у вас всё еще работает SocketIO, сразу пушим уведомление юзеру:
        socketio.emit(
            "new_notification",
            notification.to_dict(),
            room=f"user_{user_id}",  # Отправляем в персональную комнату юзера
        )
        return notification

    @staticmethod
    def get_unread_for_user(user_id):
        """Получает все непрочитанные уведомления пользователя"""
        return (
            Notification.query.filter_by(user_id=user_id, is_read=False)
            .order_by(Notification.created_at.desc())
            .all()
        )

    @staticmethod
    def mark_as_read(notification_id, user_id):
        """Помечает уведомление как прочитанное"""
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
        """Помечает все уведомления юзера как прочитанные (кнопка
        'Прочитать всё')"""
        Notification.query.filter_by(user_id=user_id, is_read=False).update(
            {"is_read": True}
        )
        db.session.commit()
