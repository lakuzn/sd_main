from app.extensions import db
from app.models.activity_log import ActivityLog


class LogService:

    @staticmethod
    def create_log(ticket_id, user_id, event_type, details):
        log = ActivityLog(
            ticket_id=ticket_id, user_id=user_id, event_type=event_type, details=details
        )
        db.session.add(log)
        return log
