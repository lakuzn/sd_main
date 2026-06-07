from app.extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    # Связи
    knowledge_articles = db.relationship("KnowledgeArticle", back_populates="category")

    def __repr__(self):
        return f"<Category #{self.name}>"
