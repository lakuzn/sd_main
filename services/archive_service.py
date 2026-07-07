from app.models import Ticket, User, Department, Category
from sqlalchemy import and_


class ArchiveCategory:
    def __init__(self, key: str, label: str, query_filter=None):
        self.key = key
        self.label = label
        self.query_filter = query_filter


class ArchiveService:
    @staticmethod
    def _my_tickets_filter(user: User):
        return Ticket.applicant_id == user.id

    @staticmethod
    def _executor_tickets_filter(user: User):
        return and_(Ticket.executors.any(id=user.id), Ticket.applicant_id != user.id)

    @staticmethod
    def _department_tickets_filter(user: User):
        if not user.department_id:
            return False
        return and_(
            Ticket.departments.any(id=user.department_id),
            Ticket.applicant_id != user.id,
            ~Ticket.executors.any(id=user.id),
        )

    @staticmethod
    def _other_tickets_filter(user: User, role: str):
        if role == "admin":
            return and_(
                Ticket.applicant_id != user.id, ~Ticket.executors.any(id=user.id)
            )
        elif role == "classifier" and user.department_id:
            return and_(
                Ticket.departments.any(id=user.department_id),
                Ticket.applicant_id != user.id,
                ~Ticket.executors.any(id=user.id),
            )
        return False

    @staticmethod
    def get_categories_for_role(role: str, user: User):
        if role == "user":
            return [
                ArchiveCategory(
                    "my", "Мои обращения", ArchiveService._my_tickets_filter
                )
            ]

        categories = [
            ArchiveCategory("my", "Мои обращения", ArchiveService._my_tickets_filter),
            ArchiveCategory(
                "executor", "Я исполнитель", ArchiveService._executor_tickets_filter
            ),
        ]

        if role in ("classifier", "head"):
            categories.append(
                ArchiveCategory(
                    "department",
                    "Заявки отдела",
                    ArchiveService._department_tickets_filter,
                )
            )
        elif role == "admin":
            categories.append(
                ArchiveCategory(
                    "other",
                    "Другие заявки",
                    lambda u: ArchiveService._other_tickets_filter(u, role),
                )
            )
        elif role == "executor":
            categories.append(
                ArchiveCategory(
                    "department",
                    "Заявки отдела",
                    ArchiveService._department_tickets_filter,
                )
            )

        categories.insert(0, ArchiveCategory("all", "Все", None))
        return categories

    @staticmethod
    def get_archive_data(user_id: int, role: str, filter_type: str = "all"):
        user = User.query.get(user_id)
        if not user:
            return {"tickets": [], "counts": {}, "current_filter": filter_type}

        base_query = Ticket.query.filter(
            Ticket.status == "Решена", Ticket.is_deleted == False
        )

        categories = ArchiveService.get_categories_for_role(role, user)
        counts = {}
        for cat in categories:
            if cat.key != "all" and cat.query_filter:
                try:
                    counts[cat.key] = base_query.filter(cat.query_filter(user)).count()
                except Exception:
                    counts[cat.key] = 0
            elif cat.key == "all":
                counts["all"] = 0

        if "all" in counts:
            counts["all"] = sum(
                counts.get(cat.key, 0) for cat in categories if cat.key != "all"
            )

        tickets = []
        if filter_type == "all":
            tickets_set = {}
            for cat in categories:
                if cat.key != "all" and cat.query_filter:
                    try:
                        cat_tickets = base_query.filter(cat.query_filter(user)).all()
                        for ticket in cat_tickets:
                            tickets_set[ticket.id] = ticket
                    except Exception:
                        continue

            tickets = list(tickets_set.values())
            tickets.sort(key=lambda t: t.updated_at, reverse=True)
        else:
            target_category = next(
                (cat for cat in categories if cat.key == filter_type), None
            )
            if target_category and target_category.query_filter:
                try:
                    tickets = (
                        base_query.filter(target_category.query_filter(user))
                        .order_by(Ticket.updated_at.desc())
                        .all()
                    )
                except Exception:
                    tickets = []

        return {"tickets": tickets, "counts": counts, "current_filter": filter_type}
