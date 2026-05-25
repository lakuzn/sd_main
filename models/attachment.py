from datetime import datetime
from app.extensions import db


class Attachment(db.Model):
    __tablename__ = "attachments"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    content_type = db.Column(db.String(100))

    # Внешние ключи
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey("messages.id"), nullable=True)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    uploaded_at = db.Column(db.DateTime, default=datetime.now)

    # Связи
    ticket = db.relationship("Ticket", back_populates="attachments")
    uploaded_by = db.relationship("User", back_populates="attachments_uploaded")

    def __repr__(self):
        return f"<Attachment {self.file_name} ({self.content_type})>"
