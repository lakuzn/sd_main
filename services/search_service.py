from sqlalchemy import or_, and_, cast, String
from app.models.ticket import Ticket
from app.models.knowledge_article import KnowledgeArticle
from app.models.category import Category
from app.models.user import User


class SearchService:

    @staticmethod
    def search_tickets(query_str, user):
        """
        Умный поиск заявок с учетом ролей.
        Ищет по ID, описанию и номеру документа.
        """
        if not query_str or not query_str.strip():
            return [], 0

        query_str = query_str.strip()
        search_term = f"%{query_str}%"

        # Базовый запрос
        base_query = Ticket.query

        # 1. ФИЛЬТРАЦИЯ ПО ПРАВАМ ДОСТУПА (Безопасность)
        if user.role == "user":
            base_query = base_query.filter(Ticket.applicant_id == user.id)
        elif user.role in ("executor", "head"):
            # Свои заявки (как заявитель) + назначенные (не решённые) + заявки отдела (не решённые)
            dept_filter = (
                and_(Ticket.departments.any(id=user.department_id), Ticket.status != "Решена")
                if user.department_id else None
            )
            assigned_filter = and_(
                Ticket.executors.any(id=user.id), Ticket.status != "Решена"
            )
            own_filter = Ticket.applicant_id == user.id
            access_filters = [own_filter, assigned_filter]
            if dept_filter is not None:
                access_filters.append(dept_filter)
            base_query = base_query.filter(or_(*access_filters))
        # Классификаторы и Админы видят всю базу (фильтр не накладываем)

        # 2. ФИЛЬТРАЦИЯ ПО ТЕКСТУ ЗАПРОСА
        # Ищем совпадения в описании или номере документа
        filters = [
            Ticket.description.ilike(search_term),
            Ticket.document_number.ilike(search_term),
        ]

        # Если ввели чистое число — ищем еще и по точному совпадению ID
        if query_str.isdigit():
            filters.append(Ticket.id == int(query_str))

        count_query = base_query.filter(or_(*filters))
        total = count_query.count()

        # Выполняем поиск и сортируем: сначала самые свежие
        results = count_query.order_by(Ticket.created_at.desc()).all()

        return results, total

    @staticmethod
    def search_articles_grouped_by_category(query_text, staff_only=True):
        """Поиск по базе знаний + группировка по категориям"""
        if not query_text:
            return {}, 0

        words = query_text.split()
        conditions = [KnowledgeArticle.title.ilike(f"%{word}%") for word in words]

        base = KnowledgeArticle.query
        if not staff_only:
            base = base.filter_by(is_staff_only=False)

        total = base.filter(or_(*conditions)).count()

        articles = base.filter(or_(*conditions)).all()
        grouped = {}
        for article in articles:
            category_name = article.category.name if article.category else "Прочее"
            grouped.setdefault(category_name, []).append(article)

        return grouped, total
