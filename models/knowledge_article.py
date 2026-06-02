from datetime import datetime
from app.extensions import db


class KnowledgeArticle(db.Model):
    __tablename__ = "knowledge_articles"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_staff_only = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    view_count = db.Column(db.Integer, default=0)

    # Внешние ключи
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    # Связи
    category = db.relationship("Category", back_populates="knowledge_articles")
    author = db.relationship("User", back_populates="knowledge_articles")

    def __repr__(self):
        return f"<Article {self.title}>"
