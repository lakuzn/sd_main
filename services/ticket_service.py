from flask import current_app, url_for
from flask_login import current_user
from app.models import (
    Ticket,
    Message,
    Attachment,
    ActivityLog,
    InternalComment,
    Department,
    Category,
    User,
)
from app.services.log_service import LogService
from app.extensions import socketio, db
import os
from datetime import datetime


class TicketService:

    @staticmethod
    def get_ticket(ticket_id):
        ticket = Ticket.query.get_or_404(ticket_id)
        return ticket

    @staticmethod
    def create_ticket(
        applicant_id, description, attachments=None, desired_deadline=None
    ):
        try:
            # Преобразование date -> db.DateTime
            if desired_deadline:
                desired_deadline = datetime.combine(
                    desired_deadline, datetime.min.time()
                )

            ticket = Ticket(
                description=description,
                applicant_id=applicant_id,
                status="Новая",
                desired_deadline=desired_deadline,
            )

            db.session.add(ticket)
            db.session.flush()  # Получаем ticket.id для привязки файлов

            if attachments and attachments[0].filename:
                TicketService._save_attachments(
                    ticket_id=ticket.id,
                    files=attachments,
                    message_id=None,
                )
            LogService.create_log(
                ticket_id=ticket.id,
                user_id=applicant_id,
                event_type="Создание заявки",
                details=f"Заяка #{ticket.id} зарегистрирована в системе",
            )

            db.session.commit()
            TicketService._emit_to_dashboards("ticket_created", ticket)

            from app.services.notification_service import NotificationService
            NotificationService.create_notification(
                user_id=applicant_id,
                message=f"Ваша заявка #{ticket.id} успешно зарегистрирована в системе.",
                ticket_id=ticket.id,
            )

            return ticket
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка создания заявки: {e}")
            raise

    @staticmethod
    def create_message(ticket_id, content, user, attachments=None):
        ticket = Ticket.query.get_or_404(ticket_id)

        msg = Message(
            content=content or "Прикрепленные файлы",
            ticket_id=ticket_id,
            sender_id=user.id,
        )

        db.session.add(msg)
        db.session.flush()  # получаем ticket.id

        # Сохранение вложений
        attachments_data = []
        if attachments and attachments[0].filename:
            attachments_data = TicketService._save_attachments(
                ticket.id, attachments, msg.id
            )

        ticket.updated_at = datetime.now()

        old_status = ticket.status
        TicketService._update_ticket_status_after_message(ticket, user.role, user)

        db.session.commit()

        # Уведомления при смене статуса из-за сообщения
        from app.services.notification_service import NotificationService
        if ticket.status == "Ожидает ответа" and old_status != "Ожидает ответа":
            # Исполнитель написал — уведомляем заявителя
            NotificationService.create_notification(
                user_id=ticket.applicant_id,
                message=f"Исполнитель ожидает вашего ответа по заявке #{ticket.id}.",
                ticket_id=ticket.id,
            )
        elif user.role == "user" and old_status == "Ожидает ответа" and ticket.status != "Ожидает ответа":
            # Заявитель ответил — уведомляем всех исполнителей
            for executor in ticket.executors:
                NotificationService.create_notification(
                    user_id=executor.id,
                    message=f"Заявитель ответил по заявке #{ticket.id}.",
                    ticket_id=ticket.id,
                )

        socketio.emit(
            "receive_message",
            {
                "id": msg.id,
                "content": msg.content,
                "sender_id": user.id,
                "sender_name": user.full_name,
                "sender_role": user.role,
                "created_at": msg.created_at.isoformat(),
                "attachments": attachments_data,
            },
            room=str(ticket_id),
        )

    @staticmethod
    def _update_ticket_status_after_message(ticket, user_role, user):
        new_status = None

        has_executors = len(ticket.executors) > 0

        if user_role in ["executor", "admin", "classifier"]:
            if has_executors and ticket.status == "В работе":
                new_status = "Ожидает ответа"
            elif not has_executors and ticket.status in ["Новая", "В обработке"]:
                new_status = "Ожидает ответа"
        elif user_role == "user":
            if ticket.status == "Ожидает ответа":
                if has_executors:
                    new_status = "В работе"
                else:
                    new_status = "В обработке"

        if new_status and new_status != ticket.status:
            TicketService.change_status(ticket, new_status, user)

    @staticmethod
    def resolve_ticket(ticket_id, user):
        ticket = Ticket.query.get_or_404(ticket_id)

        if user.id != ticket.applicant_id and user.role not in ["head", "admin"]:
            return False, "У вас нет прав для закрытия данной заявки"

        if ticket.status == "Решена":
            return False, "Заявка уже закрыта"

        ticket.status = "Решена"
        ticket.updated_at = datetime.now()

        LogService.create_log(
            ticket_id=ticket.id,
            user_id=user.id,
            event_type="Закрытие",
            details=f"Заявитель закрыл заявку #{ticket.id}",
        )

        db.session.commit()

        from app.services.notification_service import NotificationService
        for executor in ticket.executors:
            NotificationService.create_notification(
                user_id=executor.id,
                message=f"Заявитель закрыл заявку #{ticket.id} как решённую.",
                ticket_id=ticket.id,
            )

        return True, ticket

    @staticmethod
    def _save_attachments(ticket_id, files, message_id=None):
        """Вспомогательный метод - не вызывать напрямую"""

        base_upload = os.path.join(
            current_app.root_path, "static", "uploads", "tickets"
        )
        upload_folder = os.path.join(base_upload, str(ticket_id))
        os.makedirs(upload_folder, exist_ok=True)

        attachments_data = []
        for file in files:
            if not file.filename:
                continue

            original_name = file.filename
            unique_name = f"{int(datetime.now().timestamp())}_{original_name}"

            full_path = os.path.join(upload_folder, unique_name)
            file.save(full_path)

            db_path = f"uploads/tickets/{ticket_id}/{unique_name}"

            attachment = Attachment(
                file_name=original_name,
                file_path=db_path,
                file_size=os.path.getsize(full_path),
                content_type=file.mimetype or "application/octet-stream",
                ticket_id=ticket_id,
                message_id=message_id,
                uploaded_by_id=current_user.id,
            )

            db.session.add(attachment)
            db.session.flush()

            attachments_data.append(
                {
                    "id": attachment.id,
                    "file_name": original_name,
                    "file_path": db_path,
                    "url": url_for("static", filename=db_path),
                }
            )

        return attachments_data

    @staticmethod
    def get_ticket_context(ticket_id, current_user, form=None):
        """
        Возвращает полный контекст для просмотра тикета.
        Включает все данные в зависимости от роли пользователя.
        """
        ticket = Ticket.query.get_or_404(ticket_id)

        if form:
            form.priority.data = ticket.priority
            form.category_ids.data = [c.id for c in ticket.categories]
            form.executor_ids.data = [u.id for u in ticket.executors]

        messages = (
            Message.query.filter_by(ticket_id=ticket.id)
            .order_by(Message.created_at.asc())
            .all()
        )

        category_ids = [c.id for c in ticket.categories] if ticket.categories else []
        executor_ids = [c.id for c in ticket.executors] if ticket.executors else []
        department_ids = [d.id for d in ticket.departments] if ticket.departments else []

        context = {
            "ticket": ticket,
            "messages": messages,
            "comments": [],
            "categories": [],
            "departments": [],
            "executors": [],
            "form": form,
            "category_ids": category_ids,
            "executor_ids": executor_ids,
            "department_ids": department_ids,
        }

        # Если смотрит НЕ user, достаем Внутренние комментарии
        if current_user.role != "user":
            context["comments"] = (
                InternalComment.query.filter_by(ticket_id=ticket.id)
                .order_by(InternalComment.created_at.asc())
                .all()
            )

        # Если смотрит Классификатор, ему нужны списки для маршрутизации
        if current_user.role == "classifier":
            context["categories"] = Category.query.all()
            context["departments"] = Department.query.all()
            context["executors"] = User.query.filter(
                User.role.in_(["executor", "classifier"])
            ).all()

            # Меняем статус, если классификатор зашел в новую заявку
            if ticket.status == "Новая":
                ticket.status = "В обработке"
                ticket.classifier_id = current_user.id
                db.session.commit()

        # Если смотрит Начальник отдела — те же права, что у классификатора
        elif current_user.role == "head":
            context["categories"] = Category.query.all()
            context["departments"] = Department.query.all()
            context["executors"] = User.query.filter(
                User.role.in_(["executor", "head"]),
                User.department_id == current_user.department_id,
            ).all()

        return context

    @staticmethod
    def route_ticket_action(ticket_id, form, user):
        ticket = Ticket.query.get_or_404(ticket_id)

        ticket.priority = form.priority.data
        ticket.categories = Category.query.filter(
            Category.id.in_(form.category_ids.data)
        ).all()
        ticket.document_number = form.document_number.data

        if form.executor_ids.data:
            ticket.executors = User.query.filter(
                User.id.in_(form.executor_ids.data)
            ).all()
        else:
            # Если никто не выбран - назначаем нам того, кто маршрутизирует
            ticket.executors = []

        has_executors = len(ticket.executors) > 0

        if has_executors:
            if ticket.status in ["Новая", "В обработке"]:
                TicketService.change_status(ticket, "В работе", user)
        else:
            if ticket.status in ["Новая", "В работе", "Ожидает ответа"]:
                TicketService.change_status(ticket, "В обработке", user)

        LogService.create_log(
            ticket_id=ticket.id,
            user_id=user.id,
            event_type="Классификация",
            details=f"Параметры заявки #{ticket.id} изменены",
        )

        db.session.commit()

        # Уведомляем назначенных исполнителей о новой заявке
        from app.services.notification_service import NotificationService
        for executor in ticket.executors:
            NotificationService.create_notification(
                user_id=executor.id,
                message=f"Вам назначена заявка #{ticket.id}.",
                ticket_id=ticket.id,
            )

        TicketService._emit_to_dashboards(
            "ticket_updated",
            ticket,
            extra_data={
                "classified": True,
            },
        )

        return ticket

    @staticmethod
    def setup_route_form(form):
        TicketService.setup_category_choices(form)
        TicketService.setup_executor_choices(form)
        TicketService.setup_department_choices(form)
        TicketService.setup_priority_choices(form)

    @staticmethod
    def setup_category_choices(form):
        if hasattr(form, "category_ids"):
            form.category_ids.choices = [(c.id, c.name) for c in Category.query.all()]

    @staticmethod
    def setup_department_choices(form):
        if hasattr(form, "departments_id"):
            form.departments_id.choices = [(0, "Не отправлять")] + [
                (d.id, d.name) for d in Department.query.all()
            ]

    @staticmethod
    def setup_priority_choices(form):
        if hasattr(form, "priority") and not form.priority.choices:
            form.priority.choices = [
                ("Низкий", "Низкий"),
                ("Средний", "Средний"),
                ("Высокий", "Высокий"),
            ]

    @staticmethod
    def setup_executor_choices(form):

        executors = User.query.filter_by(role="executor").order_by(User.full_name).all()
        if hasattr(form, "executor_ids"):
            form.executor_ids.choices = [(u.id, u.full_name) for u in executors]

    @staticmethod
    def create_comment(ticket_id, comment, attachments=None):
        ticket = Ticket.query.get_or_404(ticket_id)

        comment = InternalComment(
            text=comment,
            ticket_id=ticket.id,
            author_id=current_user.id,
        )

        db.session.add(comment)
        db.session.flush()  # получаем ticket.id

        ticket.updated_at = datetime.now()

        LogService.create_log(
            ticket_id=ticket.id,
            user_id=current_user.id,
            event_type="Создание заявки",
            details=f"В заявку #{ticket.id} добавлен внутренний комментарий",
        )

        db.session.commit()

        socketio.emit(
            "receive_comment",
            {
                "id": comment.id,
                "text": comment.text,
                "author_id": current_user.id,
                "author_name": current_user.full_name,
                "author_role": current_user.role,
                "created_at": comment.created_at.isoformat(),
                # "attachments": attachments_data,
            },
            room=str(ticket_id),
        )

    @staticmethod
    def reassign_ticket(ticket_id, executor_ids, user):
        ticket = Ticket.query.get_or_404(ticket_id)

        # Собираем имена предыдущих исполнителей для лога
        old_names = (
            ", ".join([u.full_name for u in ticket.executors])
            if ticket.executors
            else "Никто"
        )

        # Новые исполнители
        new_executors = User.query.filter(User.id.in_(executor_ids)).all()
        new_names = (
            ", ".join([u.full_name for u in new_executors])
            if ticket.executors
            else "Никто"
        )

        ticket.executors = new_executors

        if not new_executors:
            TicketService.change_status(ticket, "В обработке", user)
            new_executors = ["Никто"]

        LogService.create_log(
            ticket_id=ticket.id,
            user_id=user.id,
            event_type="Переназначение",
            details=f"Заяку #{ticket.id} переназначили с {old_names} на {new_names}",
        )

        db.session.commit()

        # Уведомляем назначенных исполнителей
        from app.services.notification_service import NotificationService
        for executor in ticket.executors:
            NotificationService.create_notification(
                user_id=executor.id,
                message=f"Вам назначена заявка #{ticket.id}.",
                ticket_id=ticket.id,
            )

        # Новое
        TicketService._emit_to_dashboards(
            "ticket_updated",
            ticket,
            extra_data={
                "changed_executors": True,
            },
        )

        return ticket

    @staticmethod
    def change_status(ticket, new_status, user):
        """Смена статуса с автоматическим логированием"""
        old_status = ticket.status
        if old_status == new_status:
            return

        ticket.status = new_status

        # Если заявка завершена, фиксируем время решения
        if new_status == "Решена":
            ticket.resolved_at = datetime.now()

        LogService.create_log(
            ticket_id=ticket.id,
            user_id=user.id,
            event_type="Смена статуса",
            details=f"Пользователь {user.full_name} изменил статус: {old_status} -> {new_status}",
        )
        db.session.commit()

        socketio.emit(
            "ticket_status_changed",
            {
                "ticket_id": ticket.id,
                "new_status": new_status,
            },
            room=str(ticket.id),
        )

        # Новое
        TicketService._emit_to_dashboards(
            "ticket_updated",
            ticket,
            extra_data={
                "old_status": old_status,
            },
        )

    @staticmethod
    def change_params(ticket, user, **params):
        # Флаг для отслеживания, менялись ли исполнители
        executors_changed = False

        for key, value in params.items():
            if key == "categories":
                category_ids = [v for v in value if isinstance(v, int)]
                ticket.categories = Category.query.filter(
                    Category.id.in_(category_ids)
                ).all()

            elif key == "executor_ids":
                executor_ids = [v for v in value if isinstance(v, int)]
                ticket.executors = User.query.filter(User.id.in_(executor_ids)).all()
                executors_changed = True

            elif key == "department_ids":
                # Если классификатор назначает чисто на отдел (без исполнителей)
                dept_ids = [v for v in value if isinstance(v, int)]
                ticket.departments = Department.query.filter(
                    Department.id.in_(dept_ids)
                ).all()

            elif key == "desired_deadline":
                if value:
                    ticket.desired_deadline = datetime.strptime(value, "%Y-%m-%d")
                else:
                    ticket.desired_deadline = None

            elif key in ["executor_id", "departments", "categories", "messages"]:
                continue

            elif hasattr(ticket, key):
                if isinstance(value, (list, dict)):
                    continue
                setattr(ticket, key, value)

        # === УМНАЯ МАРШРУТИЗАЦИЯ ОТДЕЛОВ И СТАТУСОВ ===
        if executors_changed:
            if ticket.executors:
                # 1. Назначили людей: привязываем их уникальные отделы к заявке
                departments_set = set()
                for ex in ticket.executors:
                    if ex.department:
                        departments_set.add(ex.department)
                ticket.departments = list(departments_set)

                if ticket.status in ["Новая", "В обработке"]:
                    TicketService.change_status(ticket, "В работе", user)
            else:
                # 2. Удалили ВСЕХ исполнителей
                if ticket.departments and ticket.status in ["В работе", "Ожидает ответа"]:
                    # Возвращаем заявку в пул отдела
                    TicketService.change_status(ticket, "В обработке", user)
                elif not ticket.departments:
                    # Ни исполнителей, ни отделов — возврат в новые
                    TicketService.change_status(ticket, "Новая", user)

        # 3. Исполнителей не трогали, но назначили/сменили отдел
        elif "department_ids" in params and not ticket.executors:
            if ticket.departments and ticket.status == "Новая":
                TicketService.change_status(ticket, "В обработке", user)

        try:
            from app.extensions import db

            db.session.commit()

            LogService.create_log(
                ticket_id=ticket.id,
                user_id=user.id,
                event_type="Изменение параметров",
                details=f"Пользователь {user.full_name} обновил параметры заявки.",
            )

            socketio.emit(
                "ticket_params_changed",
                {"ticket_id": ticket.id},
                room=str(ticket.id),
            )

            TicketService._emit_to_dashboards(
                "ticket_updated",
                ticket,
                extra_data={
                    "changed_params": params,
                },
            )

            return True
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при сохранении параметров: {e}")
            return False

    @staticmethod
    def take_in_work(ticket, user):
        """Метод для самостоятельного взятия заявки из пула отдела"""
        # Проверяем, что заявка действительно направлена в отдел пользователя
        # и что на ней еще нет исполнителей
        if ticket.status == "В обработке" and user.department in ticket.departments and not ticket.executors:
            # Добавляем пользователя как исполнителя
            ticket.executors.append(user)

            # Меняем статус (функция change_status сама напишет лог и сокет)
            TicketService.change_status(ticket, "В работе", user)

            db.session.commit()

            from app.services.notification_service import NotificationService
            NotificationService.create_notification(
                user_id=ticket.applicant_id,
                message=f"Ваша заявка #{ticket.id} взята в работу исполнителем {user.full_name}.",
                ticket_id=ticket.id,
            )

            return True
        return False

    @staticmethod
    def request_review(ticket, user):
        """Исполнитель сообщает заявителю, что задача выполнена — просит проверить"""
        from app.services.notification_service import NotificationService

        TicketService.change_status(ticket, "Требует проверки", user)

        NotificationService.create_notification(
            user_id=ticket.applicant_id,
            message=f"Заявка #{ticket.id} выполнена. Требуется проверить исполнение.",
            ticket_id=ticket.id,
        )

    @staticmethod
    def reject_resolution(ticket, user):
        """Заявитель отклоняет решение и возвращает заявку в работу"""
        from app.services.notification_service import NotificationService

        new_status = "В работе" if ticket.executors else "В обработке"
        TicketService.change_status(ticket, new_status, user)

        for executor in ticket.executors:
            NotificationService.create_notification(
                user_id=executor.id,
                message=(
                    f"Заявитель отклонил решение по заявке #{ticket.id}. "
                    "Требуется доработка."
                ),
                ticket_id=ticket.id,
            )

    @staticmethod
    def assign_department(ticket, department_id, user):
        """Классификатор направляет заявку в пул отдела без конкретного исполнителя"""
        department = Department.query.get(department_id)
        if not department:
            return False

        # Назначаем отдел, снимаем исполнителей — заявка уходит в общий пул отдела
        ticket.departments = [department]
        ticket.executors = []

        LogService.create_log(
            ticket_id=ticket.id,
            user_id=user.id,
            event_type="Назначение отдела",
            details=f"Заявка #{ticket.id} направлена в отдел «{department.name}»",
        )

        # change_status делает commit если статус меняется;
        # если уже "В обработке" — возвращается без commit, делаем сами
        TicketService.change_status(ticket, "В обработке", user)
        db.session.commit()

        from app.services.notification_service import NotificationService
        if department.head_id:
            NotificationService.create_notification(
                user_id=department.head_id,
                message=f"В ваш отдел направлена заявка #{ticket.id}.",
                ticket_id=ticket.id,
            )

        TicketService._emit_to_dashboards("ticket_updated", ticket)
        return True

    @staticmethod
    def _emit_to_dashboards(event_name, ticket, extra_data=None):
        """
        Отправляет событие во все дашборды, которым интересна эта заявка.
        event_name: например 'ticket_created' или 'ticket_updated'
        ticket: объект Ticket
        extra_data: дополнительные данные (словарь)
        """
        rooms = set()
        user_id = ticket.applicant_id

        # 1. Дашборд автора (если заявка не решена – для активных, решена – для архива)
        if ticket.status != "Решена":
            rooms.add(f"dashboard_user_{user_id}")
        else:
            rooms.add(f"dashboard_archive_{user_id}")

        # 2. Дашборды исполнителей (активные заявки)
        if ticket.status != "Решена":
            for executor in ticket.executors:
                rooms.add(f"dashboard_executor_{executor.id}")

        # 3. Дашборд классификатора (для новых и в обработке)
        if ticket.status in ["Новая", "В обработке"]:
            # можно отправлять либо в персональную комнату каждого классификатора,
            # либо в общую комнату всех классификаторов (проще)
            rooms.add("dashboard_classifier_all")

        # 4. Дашборд администратора (все активные заявки)
        if ticket.status != "Решена":
            rooms.add("dashboard_admin_all")

        # 5. Для завершённых заявок – архивы исполнителей
        if ticket.status == "Решена":
            for executor in ticket.executors:
                rooms.add(f"dashboard_archive_{executor.id}")

        # 6. Дашборды начальников отделов (для заявок в их отделе)
        if ticket.status != "Решена":
            for dept in ticket.departments:
                if dept.head_id:
                    rooms.add(f"dashboard_head_{dept.head_id}")

        # Формируем данные для отправки
        ticket_dict = ticket.to_dict()  # нужно добавить метод в модель Ticket
        data = {"ticket": ticket_dict, "changed_fields": extra_data or {}}

        for room in rooms:
            socketio.emit(event_name, data, room=room)
