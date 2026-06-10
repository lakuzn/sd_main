from datetime import datetime
from app.extensions import db


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_type = db.Column(db.String(100), nullable=False)
    details = db.Column(db.String(250), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Связи
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    ticket = db.relationship("Ticket", back_populates="activity_logs")
    user = db.relationship("User", back_populates="activity_logs")

    def __repr__(self):
        return f"<Log {self.event_type} at {self.created_at}>"
