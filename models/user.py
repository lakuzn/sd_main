from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    position = db.Column(db.String(100), nullable=True)

    # РОЛИ: 'user', 'classifier', 'head', 'executor', 'admin'
    role = db.Column(db.String(20), default="user", nullable=False)

    # Привязка к отделу (nullable=True, т.к. обычным юзерам отдел может быть не нужен)
    department_id = db.Column(
        db.Integer, db.ForeignKey("departments.id"), nullable=True
    )

    # Связи
    department = db.relationship(
        "Department", foreign_keys=[department_id], back_populates="employees"
    )
    tickets_created = db.relationship(
        "Ticket", foreign_keys="Ticket.applicant_id", back_populates="applicant"
    )

    messages_sent = db.relationship("Message", back_populates="sender", lazy=True)
    activity_logs = db.relationship("ActivityLog", back_populates="user")
    knowledge_articles = db.relationship("KnowledgeArticle", back_populates="author")
    attachments_uploaded = db.relationship("Attachment", back_populates="uploaded_by")

    # Функция для создания безопасного хэша из пароля
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.full_name} ({self.email})>"
