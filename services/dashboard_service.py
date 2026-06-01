from app.models import Ticket, User
from sqlalchemy import func, or_, and_
from app.extensions import db
from datetime import datetime


class DashboardService:

    @staticmethod
    def get_user_data(user_id, page=1, per_page=18):
        """Дашборд пользователя"""

        # Заявки, где человек либо автор, либо назначен исполнителем (и она не решена)
        pagination = (
            Ticket.query.filter(
                (Ticket.applicant_id == user_id),
                Ticket.status != "Решена",
            )
            .order_by(Ticket.updated_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

        return {
            "tickets": pagination.items,
            "pagination": pagination,
        }

    @staticmethod
    def get_executor_data(user_id):
        """Дашборд агента"""

        # Ищем заявки, где текущий пользователь есть в списке исполнителей (executors)
        # и статус которых не закрыт.
        user = User.query.get(user_id)
        tickets = (
            Ticket.query.filter(
                Ticket.status != "Решена",
                or_(
                    # Заявки, где пользователь назначен исполнителем
                    Ticket.executors.any(id=user_id),
                    # Все заявки в его отделе (включая без исполнителей — для «Взять в работу»)
                    Ticket.departments.any(id=user.department_id),
                ),
            )
            .order_by(Ticket.updated_at.desc())
            .all()
        )

        return {
            "tickets": tickets,
        }

    @staticmethod
    def get_head_data(user_id):
        """Дашборд начальника отдела: все активные заявки в его отделе + лично на нём"""
        user = User.query.get(user_id)

        tickets = (
            Ticket.query.filter(
                Ticket.status != "Решена",
                or_(
                    Ticket.departments.any(id=user.department_id),
                    Ticket.executors.any(id=user_id),
                ),
            )
            .order_by(Ticket.updated_at.desc())
            .all()
        )

        return {"tickets": tickets}

    @staticmethod
    def get_classifier_data(user_id, page=1, per_page=18):
        """Дашборд классификатора"""

        pagination = (
            Ticket.query.filter(
                or_(
                    Ticket.status.in_(["Новая", "В обработке"]),
                    and_(
                        Ticket.executors.any(id=user_id),
                        Ticket.status != "Решена",
                    ),
                )
            )
            .order_by(Ticket.updated_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

        return {"tickets": pagination.items, "pagination": pagination}

    @staticmethod
    def get_archive_data(user_id, user_role):
        """Дашборд архивных заявок"""

        context = {
            "executor_tasks_solved": [],
            "tickets": [],
        }

        if user_role == "executor":
            context["tickets"] = (
                Ticket.query.filter(
                    Ticket.applicant_id == user_id,
                    Ticket.status == "Решена",
                    Ticket.is_deleted == False,
                )
                .order_by(Ticket.updated_at.desc())
                .all()
            )

            context["executor_tasks_solved"] = (
                Ticket.query.filter(
                    Ticket.executors.any(id=user_id),
                    Ticket.status == "Решена",
                    Ticket.is_deleted == False,
                )
                .order_by(Ticket.updated_at.desc())
                .all()
            )

        else:
            context["tickets"] = (
                Ticket.query.filter(
                    Ticket.applicant_id == user_id,
                    Ticket.status == "Решена",
                    Ticket.is_deleted == False,
                )
                .order_by(Ticket.updated_at.desc())
                .all()
            )

        return context
