from sqlalchemy import or_, and_, cast, String
from app.models.ticket import Ticket
from app.models.knowledge_article import KnowledgeArticle
from app.models.category import Category
from app.models.user import User


class SearchService:

    @staticmethod
    def search_tickets(query_str, user):
        if not query_str or not query_str.strip():
            return [], 0

        query_str = query_str.strip()
        search_term = f"%{query_str}%"

        base_query = Ticket.query

        if user.role == "user":
            base_query = base_query.filter(Ticket.applicant_id == user.id)
        elif user.role in ("executor", "head"):
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
        filters = [
            Ticket.description.ilike(search_term),
            Ticket.document_number.ilike(search_term),
        ]

        if query_str.isdigit():
            filters.append(Ticket.id == int(query_str))

        count_query = base_query.filter(or_(*filters))
        total = count_query.count()

        results = count_query.order_by(Ticket.created_at.desc()).all()

        return results, total

    @staticmethod
    def search_articles_grouped_by_category(query_text, staff_only=True):
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
