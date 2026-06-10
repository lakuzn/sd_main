from app.services.notification_service import NotificationService
from flask_login import current_user
from app.blueprints.notifications import notifications_bp


@notifications_bp.app_context_processor
def inject_notifications():
    if current_user.is_authenticated:
        notifications = NotificationService.get_unread_for_user(current_user.id)
        return dict(notifications=notifications, unread_count=len(notifications))
    return dict(notifications=[], unread_count=0)
