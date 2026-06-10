from datetime import datetime
from app.extensions import db


class TicketView(db.Model):
    """Когда конкретный пользователь последний раз открывал заявку.

    Используется, чтобы показывать индикатор новых сообщений на карточке:
    если в заявке появилось сообщение позже, чем пользователь её открывал,
    значит для него есть непрочитанные сообщения.
    """

    __tablename__ = "ticket_views"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    last_viewed_at = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint("ticket_id", "user_id", name="uq_ticket_view"),
    )
