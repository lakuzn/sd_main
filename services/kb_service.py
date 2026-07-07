from app.models.knowledge_article import KnowledgeArticle
from app.models.category import Category
from app.services.log_service import LogService


class KBService:

    @staticmethod
    def get_all_articles_grouped_by_category(staff_only=True):
        query = KnowledgeArticle.query
        if not staff_only:
            query = query.filter_by(is_staff_only=False)
        articles = query.order_by(KnowledgeArticle.title).all()

        grouped = {}
        for article in articles:
            cat_name = article.category.name if article.category else "Прочее"

            if cat_name not in grouped:
                grouped[cat_name] = []

            grouped[cat_name].append(article)

        return grouped

    @staticmethod
    def get_article_by_id(article_id):
        return KnowledgeArticle.query.get_or_404(article_id)

    @staticmethod
    def can_edit(article, user):
        return user.role == "admin" or article.author_id == user.id

    @staticmethod
    def create_article(title, content, category_id, is_staff_only, author_id):
        from app.extensions import db
        from app.models.knowledge_article import KnowledgeArticle

        article = KnowledgeArticle(
            title=title,
            content=content,
            category_id=category_id,
            is_staff_only=is_staff_only,
            author_id=author_id,
        )
        db.session.add(article)
        db.session.flush()
        LogService.create_log(
            ticket_id=None,
            user_id=author_id,
            event_type="Создание статьи в БЗ",
            details=f"Статья #{article.id} зарегистрирована в системе",
        )
        db.session.commit()

        return article

    @staticmethod
    def update_article(article_id, title, content, category_id, is_staff_only, editor):
        from app.extensions import db

        article = KnowledgeArticle.query.get_or_404(article_id)

        article.title = title
        article.content = content
        article.category_id = category_id
        article.is_staff_only = is_staff_only

        LogService.create_log(
            ticket_id=None,
            user_id=editor.id,
            event_type="Изменение статьи в БЗ",
            details=f"Статья #{article.id} отредактирована ({editor.full_name})",
        )

        db.session.commit()

        return article

    @staticmethod
    def delete_article(article_id, user):
        from app.extensions import db

        article = KnowledgeArticle.query.get_or_404(article_id)

        LogService.create_log(
            ticket_id=None,
            user_id=user.id,
            event_type="Удаление статьи в БЗ",
            details=f"Статья #{article.id} «{article.title}» удалена ({user.full_name})",
        )

        db.session.delete(article)
        db.session.commit()
