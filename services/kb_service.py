from app.models.knowledge_article import KnowledgeArticle
from app.models.category import Category
from app.services.log_service import LogService


class KBService:

    @staticmethod
    def get_all_articles_grouped_by_category():
        """Возвращает статьи, сгрупированные по категориям"""
        articles = KnowledgeArticle.query.order_by(KnowledgeArticle.title).all()

        grouped = {}
        for article in articles:
            cat_name = article.category.name if article.category else "Прочее"

            if cat_name not in grouped:
                grouped[cat_name] = []

            grouped[cat_name].append(article)

        return grouped

    @staticmethod
    def get_article_by_id(article_id):
        """Получить одну статью"""
        return KnowledgeArticle.query.get_or_404(article_id)

    @staticmethod
    def create_article(title, content, category_id, is_staff_only, author_id):
        """Создание новой статьи в Базе Знаний"""
        from app.extensions import db
        from app.models.knowledge_article import KnowledgeArticle

        article = KnowledgeArticle(
            title=title,
            content=content,  # Сюда прилетит готовый HTML-код от редактора
            category_id=category_id,
            is_staff_only=is_staff_only,
            author_id=author_id,
        )
        db.session.add(article)

        LogService.create_log(
            ticket_id=1,
            user_id=author_id,
            event_type="Создание статьи в БЗ",
            details=f"Статья #{article.id} зарегистрирована в системе",
        )

        db.session.commit()

        return article
