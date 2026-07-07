from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models.department import head_managed_departments


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(50), nullable=True, default="Не указан")
    password_hash = db.Column(db.String(255), nullable=True)
    position = db.Column(db.String(255), nullable=True)

    username = db.Column(db.String(150), unique=True, nullable=True, index=True)
    ad_guid = db.Column(db.String(64), unique=True, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_sync_at = db.Column(db.DateTime, nullable=True)

    host_name = db.Column(db.String(255), nullable=True)

    role = db.Column(db.String(20), default="user", nullable=False)

    department_id = db.Column(
        db.Integer, db.ForeignKey("departments.id"), nullable=True
    )

    # Связи
    department = db.relationship(
        "Department", foreign_keys=[department_id], back_populates="employees"
    )
    managed_departments = db.relationship(
        "Department",
        secondary=head_managed_departments,
        backref=db.backref("extra_heads", lazy="dynamic"),
    )
    tickets_created = db.relationship(
        "Ticket", foreign_keys="Ticket.applicant_id", back_populates="applicant"
    )

    messages_sent = db.relationship("Message", back_populates="sender", lazy=True)
    activity_logs = db.relationship("ActivityLog", back_populates="user")
    knowledge_articles = db.relationship("KnowledgeArticle", back_populates="author")
    attachments_uploaded = db.relationship("Attachment", back_populates="uploaded_by")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.full_name} ({self.email})>"
