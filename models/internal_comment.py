from datetime import datetime
from app.extensions import db


class InternalComment(db.Model):
    __tablename__ = "internal_comments"

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Связи
    ticket = db.relationship("Ticket", back_populates="internal_comments")
    author = db.relationship("User", foreign_keys=[author_id])
    attachments = db.relationship(
        "Attachment",
        backref="comment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
