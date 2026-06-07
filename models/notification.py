from app.extensions import db
from datetime import datetime


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Связи
    ticket = db.relationship("Ticket")
    user = db.relationship(
        "User",
        backref=db.backref(
            "notifications", lazy="dynamic", cascade="all, delete-orphan"
        ),
    )

    def to_dict(self):
        # Отдача данных в json
        return {
            "id": self.id,
            "message": self.message,
            "ticket_id": self.ticket_id,
            "is_read": self.is_read,
            "created_at": self.created_at.strftime("%d.%m.%Y %H:%M"),
        }
