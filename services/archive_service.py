from app.models import Ticket, User, Department, Category
from sqlalchemy import and_


class ArchiveCategory:
    """Класс для представления категории фильтрации"""

    def __init__(self, key: str, label: str, query_filter=None):
        self.key = key
        self.label = label
        self.query_filter = query_filter


class ArchiveService:
    """Сервис для работы с архивными заявками"""

    @staticmethod
    def _my_tickets_filter(user: User):
        """Фильтр для моих обращений"""
        return Ticket.applicant_id == user.id

    @staticmethod
    def _executor_tickets_filter(user: User):
        """Фильтр для заявок, где я исполнитель"""
        return and_(Ticket.executors.any(id=user.id), Ticket.applicant_id != user.id)

    @staticmethod
    def _department_tickets_filter(user: User):
        """Фильтр для заявок отдела (для head и executor)"""
        if not user.department_id:
            return False
        return and_(
            Ticket.departments.any(id=user.department_id),
            Ticket.applicant_id != user.id,
            ~Ticket.executors.any(id=user.id),
        )

    @staticmethod
    def _other_tickets_filter(user: User, role: str):
        """Фильтр для других заявок (для classifier/admin)"""
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
        """Возвращает список доступных категорий для роли"""
        if role == "user":
            return [
                ArchiveCategory(
                    "my", "Мои обращения", ArchiveService._my_tickets_filter
                )
            ]

        # Базовые категории для всех ролей, кроме user
        categories = [
            ArchiveCategory("my", "Мои обращения", ArchiveService._my_tickets_filter),
            ArchiveCategory(
                "executor", "Я исполнитель", ArchiveService._executor_tickets_filter
            ),
        ]

        # Дополнительные категории в зависимости от роли
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
            # Исполнитель тоже видит заявки отдела по ТЗ
            categories.append(
                ArchiveCategory(
                    "department",
                    "Заявки отдела",
                    ArchiveService._department_tickets_filter,
                )
            )

        # Добавляем категорию 'all' в начало для удобства
        categories.insert(0, ArchiveCategory("all", "Все", None))
        return categories

    @staticmethod
    def get_archive_data(user_id: int, role: str, filter_type: str = "all"):
        """
        Получение данных архива с учётом роли и фильтра

        Args:
            user_id: ID пользователя
            role: роль пользователя
            filter_type: тип фильтра ('all', 'my', 'executor', 'department', 'other')

        Returns:
            dict: {
                'tickets': list,  # список тикетов для текущего фильтра
                'counts': dict,   # счётчики по всем категориям
                'current_filter': str  # текущий тип фильтра
            }
        """
        user = User.query.get(user_id)
        if not user:
            return {"tickets": [], "counts": {}, "current_filter": filter_type}

        base_query = Ticket.query.filter(
            Ticket.status == "Решена", Ticket.is_deleted == False
        )

        # Получаем доступные категории для роли
        categories = ArchiveService.get_categories_for_role(role, user)

        # Вычисляем счётчики для всех категорий
        counts = {}
        for cat in categories:
            if cat.key != "all" and cat.query_filter:
                try:
                    counts[cat.key] = base_query.filter(cat.query_filter(user)).count()
                except Exception:
                    counts[cat.key] = 0
            elif cat.key == "all":
                counts["all"] = 0

        # Считаем общее количество для 'all'
        if "all" in counts:
            counts["all"] = sum(
                counts.get(cat.key, 0) for cat in categories if cat.key != "all"
            )

        # Получаем список тикетов для запрошенного фильтра
        tickets = []
        if filter_type == "all":
            # Объединяем тикеты из всех категорий, исключая дубликаты
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
            # Сортируем по дате обновления (новые сверху)
            tickets.sort(key=lambda t: t.updated_at, reverse=True)
        else:
            # Ищем категорию с нужным ключом
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
