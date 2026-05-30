from datetime import datetime
from app.extensions import db


ticket_executors = db.Table(
    "ticket_executors",
    db.Column(
        "ticket_id",
        db.Integer,
        db.ForeignKey("tickets.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "user_id",
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

ticket_categories = db.Table(
    "ticket_categories",
    db.Column(
        "ticket_id",
        db.Integer,
        db.ForeignKey("tickets.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "category_id",
        db.Integer,
        db.ForeignKey("categories.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

ticket_departments = db.Table(
    "ticket_departments",
    db.Column(
        "ticket_id",
        db.Integer,
        db.ForeignKey("tickets.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "department_id",
        db.Integer,
        db.ForeignKey("departments.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)

    status = db.Column(db.String(50), default="Новая", nullable=False)

    # Приоритет теперь может быть пустым при создании (его ставит Классификатор)
    priority = db.Column(db.String(20), default="Без приоритета", nullable=True)

    # Для классификатора, номер документа (служебной записки, приказа)
    document_number = db.Column(db.String(100), nullable=True)

    # Сроки
    desired_deadline = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Мягкое удаление (заявка скрывается от пользователей, но остаётся в БД)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Внешние ключи (кто создал и на кого назначена)
    applicant_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    classifier_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )  # Кто классифицировал

    # СВЯЗИ
    applicant = db.relationship(
        "User", foreign_keys=[applicant_id], back_populates="tickets_created"
    )
    classifier = db.relationship("User", foreign_keys=[classifier_id])
    departments = db.relationship(
        "Department",
        secondary=ticket_departments,
        backref=db.backref("tickets_in_pool", lazy="dynamic"),
    )
    categories = db.relationship(
        "Category",
        secondary=ticket_categories,
        lazy="subquery",
        backref=db.backref("tickets", lazy="dynamic"),
    )
    internal_comments = db.relationship(
        "InternalComment",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="InternalComment.created_at.desc()",
    )
    messages = db.relationship(
        "Message", back_populates="ticket", cascade="all, delete-orphan"
    )
    attachments = db.relationship(
        "Attachment", back_populates="ticket", cascade="all, delete-orphan"
    )
    executors = db.relationship(
        "User",
        secondary=ticket_executors,
        lazy="subquery",
        backref=db.backref("assigned_tickets", lazy="dynamic"),
    )

    activity_logs = db.relationship(
        "ActivityLog", back_populates="ticket", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Ticket #{self.id} | {self.status}>"

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "applicant_id": self.applicant_id,
            "applicant_name": self.applicant.full_name if self.applicant else "",
            "executor_ids": [e.id for e in self.executors],
            "department_ids": [dep.id for dep in self.departments],
            "executor_names": [e.full_name for e in self.executors],
            "category_names": [c.name for c in self.categories],
        }
