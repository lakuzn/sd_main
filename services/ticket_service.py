from flask import current_app, url_for, abort
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
    TicketView,
)
from app.services.log_service import LogService
from app.extensions import socketio, db
from werkzeug.utils import secure_filename
import os
from datetime import datetime


class TicketService:

    @staticmethod
    def get_ticket(ticket_id):
        ticket = Ticket.query.get_or_404(ticket_id)
        return ticket

    @staticmethod
    def _recipients(ticket, exclude_id=None):
        """Все заинтересованные по заявке: заявитель, исполнители, начальники
        отделов. Нужно, чтобы события заявки доходили до всех её участников.

        exclude_id — id того, кто сам совершил действие (ему уведомление не шлём).
        """
        ids = set()
        if ticket.applicant_id:
            ids.add(ticket.applicant_id)
        for ex in ticket.executors:
            ids.add(ex.id)
        for dep in ticket.departments:
            if dep.head_id:
                ids.add(dep.head_id)
        ids.discard(exclude_id)
        return ids

    @staticmethod
    def _notify(ticket, message, actor_id=None):
        """Уведомляет всех участников заявки, кроме инициатора действия."""
        from app.services.notification_service import NotificationService
        NotificationService.notify_many(
            TicketService._recipients(ticket, exclude_id=actor_id),
            message,
            ticket.id,
        )

    @staticmethod
    def mark_ticket_viewed(ticket_id, user_id):
        """Запоминаем, что пользователь открыл заявку — индикатор новых сообщений гаснет."""
        view = TicketView.query.filter_by(
            ticket_id=ticket_id, user_id=user_id
        ).first()

        if view:
            view.last_viewed_at = datetime.now()
        else:
            view = TicketView(
                ticket_id=ticket_id,
                user_id=user_id,
                last_viewed_at=datetime.now(),
            )
            db.session.add(view)

        db.session.commit()

    @staticmethod
    def get_unread_ticket_ids(tickets, user_id):
        """Возвращает множество id заявок, в которых есть новые (непрочитанные) сообщения."""
        tickets_with_msg = [t for t in tickets if t.last_message_at]
        if not tickets_with_msg:
            return set()

        ticket_ids = [t.id for t in tickets_with_msg]
        views = {
            v.ticket_id: v.last_viewed_at
            for v in TicketView.query.filter(
                TicketView.user_id == user_id,
                TicketView.ticket_id.in_(ticket_ids),
            ).all()
        }

        unread = set()
        for t in tickets_with_msg:
            last_viewed = views.get(t.id)
            if last_viewed is None or last_viewed < t.last_message_at:
                unread.add(t.id)

        return unread

    @staticmethod
    def can_access_ticket(ticket, user):
        """Проверяет, имеет ли пользователь доступ к ПРОСМОТРУ заявки.

        Право на просмотр не даёт права писать или менять заявку — это
        проверяется отдельно в соответствующих обработчиках.
        """
        if user.role == "admin":
            return True

        if ticket.is_deleted:
            return False

        # Заявитель всегда видит свою заявку
        if user.id == ticket.applicant_id:
            return True

        # Назначенный исполнитель видит заявку
        if user in ticket.executors:
            return True

        # Классификатор (первая линия) видит все заявки
        if user.role == "classifier":
            return True

        # Исполнитель и начальник отдела видят все заявки своего отдела —
        # чтобы помочь коллегам или взять заявку в работу
        if user.role in ["executor", "head"] and user.department_id:
            for dept in ticket.departments:
                if dept.id == user.department_id:
                    return True

        return False

    @staticmethod
    def delete_ticket(ticket_id, user):
        """Мягкое удаление — заявка скрывается от пользователей, но остаётся в БД."""
        ticket = Ticket.query.get_or_404(ticket_id)

        if user.id != ticket.applicant_id and user.role != "admin":
            return False, "У вас нет прав для удаления этой заявки"

        ticket.is_deleted = True
        ticket.deleted_at = datetime.now()

        LogService.create_log(
            ticket_id=ticket.id,
            user_id=user.id,
            event_type="Удаление",
            details=f"Заявка #{ticket.id} скрыта пользователем {user.full_name}",
        )

        db.session.commit()

        # Если заявку удалил не сам заявитель (например, администратор) —
        # сообщаем заявителю. Без ссылки на заявку, т.к. она уже скрыта.
        if user.id != ticket.applicant_id:
            from app.services.notification_service import NotificationService
            NotificationService.create_notification(
                user_id=ticket.applicant_id,
                message=f"Заявка #{ticket.id} была удалена.",
                ticket_id=None,
            )

        return True, ticket

    @staticmethod
    def clone_ticket(ticket_id, user):
        """Создаёт новую заявку на основе существующей (та остаётся без изменений).

        Обычный пользователь создаёт «похожую» заявку от своего имени (копируются
        описание, категории, приоритет, срок). Классификатор / начальник / админ
        может полностью продублировать заявку с сохранением всех полей —
        заявителя, исполнителей, отделов, номера документа и т.д.
        """
        original = Ticket.query.get_or_404(ticket_id)

        is_staff_clone = user.role in ["classifier", "head", "admin"]
        applicant_id = original.applicant_id if is_staff_clone else user.id

        new_ticket = Ticket(
            description=original.description,
            applicant_id=applicant_id,
            status="Новая",
            priority=original.priority,
            desired_deadline=original.desired_deadline,
            host_name=original.host_name,
        )

        if is_staff_clone:
            # Полный дубликат: сохраняем номер документа и закрепляем классификатора
            new_ticket.document_number = original.document_number
            new_ticket.classifier_id = user.id

        db.session.add(new_ticket)
        db.session.flush()

        # Связи many-to-many назначаем после добавления заявки в сессию
        new_ticket.categories = list(original.categories)

        if is_staff_clone:
            new_ticket.executors = list(original.executors)
            new_ticket.departments = list(original.departments)

            # Приводим статус в соответствие с назначениями
            if new_ticket.executors:
                new_ticket.status = "В работе"
            elif new_ticket.departments:
                new_ticket.status = "В обработке"

        LogService.create_log(
            ticket_id=new_ticket.id,
            user_id=user.id,
            event_type="Создание заявки",
            details=f"Заявка #{new_ticket.id} создана как похожая на #{original.id}",
        )

        db.session.commit()

        TicketService._emit_to_dashboards("ticket_created", new_ticket)

        from app.services.notification_service import NotificationService
        NotificationService.create_notification(
            user_id=new_ticket.applicant_id,
            message=f"Ваша заявка #{new_ticket.id} успешно зарегистрирована в системе.",
            ticket_id=new_ticket.id,
        )
        for executor in new_ticket.executors:
            NotificationService.create_notification(
                user_id=executor.id,
                message=f"Вам назначена заявка #{new_ticket.id}.",
                ticket_id=new_ticket.id,
            )

        return new_ticket

    @staticmethod
    def create_ticket(
        applicant_id,
        description,
        attachments=None,
        desired_deadline=None,
        host_name=None,
    ):
        try:
            if desired_deadline:
                desired_deadline = datetime.combine(
                    desired_deadline, datetime.min.time()
                )

            ticket = Ticket(
                description=description,
                applicant_id=applicant_id,
                status="Новая",
                desired_deadline=desired_deadline,
                host_name=(host_name or None),
            )

            db.session.add(ticket)
            db.session.flush()

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
        db.session.flush()

        attachments_data = []
        if attachments and attachments[0].filename:
            attachments_data = TicketService._save_attachments(
                ticket.id, attachments, msg.id
            )

        ticket.updated_at = datetime.now()
        ticket.last_message_at = datetime.now()

        old_status = ticket.status
        TicketService._update_ticket_status_after_message(ticket, user.role, user)

        db.session.commit()

        # Для самого отправителя сообщение сразу считается прочитанным
        TicketService.mark_ticket_viewed(ticket.id, user.id)

        from app.services.notification_service import NotificationService
        if ticket.status == "Ожидает ответа" and old_status != "Ожидает ответа":
            NotificationService.create_notification(
                user_id=ticket.applicant_id,
                message=f"Исполнитель ожидает вашего ответа по заявке #{ticket.id}.",
                ticket_id=ticket.id,
            )
        elif user.role == "user" and old_status == "Ожидает ответа" and ticket.status != "Ожидает ответа":
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
                "sender_position": user.position or "",
                "created_at": msg.created_at.isoformat(),
                "attachments": attachments_data,
            },
            room=str(ticket_id),
        )

        # Оповещаем дашборды о новом сообщении
        TicketService._emit_to_dashboards(
            "ticket_updated",
            ticket,
            extra_data={"new_message": True},
        )

    @staticmethod
    def _update_ticket_status_after_message(ticket, user_role, user):
        new_status = None

        has_executors = len(ticket.executors) > 0

        # Если пишет сам заявитель (даже если по роли он исполнитель/классификатор,
        # но это его собственная заявка) — ведём себя как с обычным пользователем
        if user.id == ticket.applicant_id and user not in ticket.executors:
            user_role = "user"

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

        ticket.updated_at = datetime.now()

        # Смена статуса через change_status — рассылает сокет-события в комнату заявки
        # (новый статус и кнопки) и обновляет дашборды/архив участников.
        TicketService.change_status(ticket, "Решена", user)

        LogService.create_log(
            ticket_id=ticket.id,
            user_id=user.id,
            event_type="Закрытие",
            details=f"Заявка #{ticket.id} закрыта ({user.full_name})",
        )
        db.session.commit()

        TicketService._notify(
            ticket,
            f"Заявка #{ticket.id} закрыта как решённая.",
            actor_id=user.id,
        )

        return True, ticket

    @staticmethod
    def _save_attachments(ticket_id, files, message_id=None, comment_id=None):
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
            # Имя файла на диске обеззараживаем (защита от выхода за пределы
            # папки загрузок), оригинальное имя сохраняем для отображения.
            safe_name = secure_filename(original_name) or "file"
            unique_name = f"{int(datetime.now().timestamp())}_{safe_name}"

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
                comment_id=comment_id,
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
            "logs": [],
            "form": form,
            "category_ids": category_ids,
            "executor_ids": executor_ids,
            "department_ids": department_ids,
        }

        if current_user.role != "user":
            context["comments"] = (
                InternalComment.query.filter_by(ticket_id=ticket.id)
                .order_by(InternalComment.created_at.asc())
                .all()
            )
            # История событий по заявке (журнал) — показываем сотрудникам
            context["logs"] = (
                ActivityLog.query.filter_by(ticket_id=ticket.id)
                .order_by(ActivityLog.created_at.desc())
                .limit(50)
                .all()
            )

        if current_user.role == "classifier":
            context["categories"] = Category.query.all()
            context["departments"] = Department.query.all()
            context["executors"] = User.query.filter(
                User.role.in_(["executor", "classifier"])
            ).all()

            if ticket.status == "Новая":
                ticket.status = "В обработке"
                ticket.classifier_id = current_user.id
                db.session.commit()

        elif current_user.role == "head":
            context["categories"] = Category.query.all()
            context["departments"] = Department.query.all()
            context["executors"] = User.query.filter(
                User.role.in_(["executor", "head"]),
                User.department_id == current_user.department_id,
            ).all()

        elif current_user.role == "admin":
            context["categories"] = Category.query.all()
            context["departments"] = Department.query.all()
            context["executors"] = User.query.filter(
                User.role.in_(["executor", "head"])
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

        from app.services.notification_service import NotificationService
        for executor in ticket.executors:
            NotificationService.create_notification(
                user_id=executor.id,
                message=f"Вам назначена заявка #{ticket.id}.",
                ticket_id=ticket.id,
            )

        # Уведомляем заявителя о том, что его заявка обработана
        if user.id != ticket.applicant_id:
            status_msg = (
                f"Ваша заявка #{ticket.id} передана в работу."
                if has_executors
                else f"Ваша заявка #{ticket.id} принята в обработку."
            )
            NotificationService.create_notification(
                user_id=ticket.applicant_id,
                message=status_msg,
                ticket_id=ticket.id,
            )

        TicketService._emit_to_dashboards(
            "ticket_updated",
            ticket,
            extra_data={"classified": True},
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
        # В исполнители можно назначить исполнителей, начальников и классификаторов —
        # именно их показывают в выпадающем списке на странице заявки.
        executors = (
            User.query.filter(User.role.in_(["executor", "head", "classifier"]))
            .order_by(User.full_name)
            .all()
        )
        if hasattr(form, "executor_ids"):
            form.executor_ids.choices = [(u.id, u.full_name) for u in executors]

    @staticmethod
    def create_comment(ticket_id, comment, attachments=None):
        ticket = Ticket.query.get_or_404(ticket_id)

        new_comment = InternalComment(
            text=comment,
            ticket_id=ticket.id,
            author_id=current_user.id,
        )

        db.session.add(new_comment)
        db.session.flush()

        attachments_data = []
        if attachments and attachments[0].filename:
            attachments_data = TicketService._save_attachments(
                ticket.id, attachments, message_id=None, comment_id=new_comment.id
            )

        ticket.updated_at = datetime.now()

        LogService.create_log(
            ticket_id=ticket.id,
            user_id=current_user.id,
            event_type="Внутренний комментарий",
            details=f"В заявку #{ticket.id} добавлен внутренний комментарий",
        )

        db.session.commit()

        socketio.emit(
            "receive_comment",
            {
                "id": new_comment.id,
                "text": new_comment.text,
                "author_id": current_user.id,
                "author_name": current_user.full_name,
                "author_role": current_user.role,
                "created_at": new_comment.created_at.isoformat(),
                "attachments": attachments_data,
            },
            room=f"ticket_staff_{ticket_id}",
        )

        # Внутренний комментарий — служебная переписка, поэтому уведомляем
        # только сотрудников по заявке (исполнителей и начальника отдела),
        # но не самого заявителя.
        from app.services.notification_service import NotificationService
        recipients = {ex.id for ex in ticket.executors}
        for dep in ticket.departments:
            if dep.head_id:
                recipients.add(dep.head_id)
        recipients.discard(current_user.id)
        NotificationService.notify_many(
            recipients,
            f"Новый внутренний комментарий по заявке #{ticket.id}.",
            ticket.id,
        )

    @staticmethod
    def reassign_ticket(ticket_id, executor_ids, user):
        ticket = Ticket.query.get_or_404(ticket_id)

        old_names = (
            ", ".join([u.full_name for u in ticket.executors])
            if ticket.executors
            else "Никто"
        )

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

        from app.services.notification_service import NotificationService
        for executor in ticket.executors:
            NotificationService.create_notification(
                user_id=executor.id,
                message=f"Вам назначена заявка #{ticket.id}.",
                ticket_id=ticket.id,
            )

        if user.id != ticket.applicant_id:
            NotificationService.create_notification(
                user_id=ticket.applicant_id,
                message=f"По заявке #{ticket.id} изменён состав исполнителей.",
                ticket_id=ticket.id,
            )

        TicketService._emit_to_dashboards(
            "ticket_updated",
            ticket,
            extra_data={"changed_executors": True},
        )

        return ticket

    @staticmethod
    def change_status(ticket, new_status, user):
        """Смена статуса с автоматическим логированием"""
        old_status = ticket.status
        if old_status == new_status:
            return

        ticket.status = new_status

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

        TicketService._emit_to_dashboards(
            "ticket_updated",
            ticket,
            extra_data={"old_status": old_status},
        )

    @staticmethod
    def change_params(ticket, user, **params):
        executors_changed = False
        old_executor_ids = {ex.id for ex in ticket.executors}

        for key, value in params.items():
            if key == "categories":
                category_ids = [v for v in value if isinstance(v, int)]
                ticket.categories = Category.query.filter(
                    Category.id.in_(category_ids)
                ).all()

            elif key == "executor_ids":
                executor_ids = [v for v in value if isinstance(v, int)]
                ticket.executors = User.query.filter(User.id.in_(executor_ids)).all()
                # Если назначаем исполнителей — снимаем явную привязку к отделам
                if executor_ids:
                    ticket.departments = []
                executors_changed = True

            elif key == "department_ids":
                dept_ids = [v for v in value if isinstance(v, int)]
                ticket.departments = Department.query.filter(
                    Department.id.in_(dept_ids)
                ).all()
                # Если назначаем отдел — снимаем исполнителей
                if dept_ids:
                    ticket.executors = []

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

        # === УМНАЯ МАРШРУТИЗАЦИЯ СТАТУСОВ ===
        if executors_changed:
            if ticket.executors:
                # Назначили исполнителей — привязываем их отделы
                departments_set = set()
                for ex in ticket.executors:
                    if ex.department:
                        departments_set.add(ex.department)
                ticket.departments = list(departments_set)

                if ticket.status in ["Новая", "В обработке"]:
                    TicketService.change_status(ticket, "В работе", user)
            else:
                if ticket.departments and ticket.status in ["В работе", "Ожидает ответа"]:
                    TicketService.change_status(ticket, "В обработке", user)
                elif not ticket.departments:
                    TicketService.change_status(ticket, "Новая", user)

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
                {
                    "ticket_id": ticket.id,
                    "new_status": ticket.status,
                    "executor_ids": [ex.id for ex in ticket.executors],
                    "department_ids": [d.id for d in ticket.departments],
                    "category_ids": [c.id for c in ticket.categories],
                    "priority": ticket.priority,
                },
                room=str(ticket.id),
            )

            TicketService._emit_to_dashboards(
                "ticket_updated",
                ticket,
                extra_data={"changed_params": list(params.keys())},
            )

            # Уведомляем вновь назначенных исполнителей (если состав менялся)
            if executors_changed:
                from app.services.notification_service import NotificationService
                added = {ex.id for ex in ticket.executors} - old_executor_ids
                for uid in added:
                    NotificationService.create_notification(
                        user_id=uid,
                        message=f"Вам назначена заявка #{ticket.id}.",
                        ticket_id=ticket.id,
                    )

            return True
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при сохранении параметров: {e}")
            return False

    @staticmethod
    def take_in_work(ticket, user):
        """Метод для самостоятельного взятия заявки из пула отдела"""
        if ticket.status == "В обработке" and user.department in ticket.departments and not ticket.executors:
            ticket.executors.append(user)

            # Заявка закрепляется за отделом того, кто взял её в работу
            if user.department:
                ticket.departments = [user.department]

            TicketService.change_status(ticket, "В работе", user)

            LogService.create_log(
                ticket_id=ticket.id,
                user_id=user.id,
                event_type="Взятие в работу",
                details=f"{user.full_name} взял заявку #{ticket.id} в работу",
            )
            db.session.commit()

            TicketService._notify(
                ticket,
                f"{user.full_name} взял заявку #{ticket.id} в работу.",
                actor_id=user.id,
            )

            return True
        return False

    @staticmethod
    def request_review(ticket, user):
        """Исполнитель сообщает заявителю, что задача выполнена — просит проверить"""
        TicketService.change_status(ticket, "Требует проверки", user)

        LogService.create_log(
            ticket_id=ticket.id,
            user_id=user.id,
            event_type="Запрос проверки",
            details=f"Исполнитель {user.full_name} запросил проверку по заявке #{ticket.id}",
        )
        db.session.commit()

        TicketService._notify(
            ticket,
            f"Заявка #{ticket.id} выполнена — требуется проверка заявителем.",
            actor_id=user.id,
        )

    @staticmethod
    def reject_resolution(ticket, user):
        """Заявитель отклоняет решение и возвращает заявку в работу"""
        new_status = "В работе" if ticket.executors else "В обработке"
        TicketService.change_status(ticket, new_status, user)

        LogService.create_log(
            ticket_id=ticket.id,
            user_id=user.id,
            event_type="Отклонение решения",
            details=f"Заявитель отклонил решение по заявке #{ticket.id}",
        )
        db.session.commit()

        TicketService._notify(
            ticket,
            f"Заявитель отклонил решение по заявке #{ticket.id} — требуется доработка.",
            actor_id=user.id,
        )

    @staticmethod
    def assign_department(ticket, department_id, user):
        """Классификатор направляет заявку в пул отдела без конкретного исполнителя"""
        department = Department.query.get(department_id)
        if not department:
            return False

        ticket.departments = [department]
        ticket.executors = []

        LogService.create_log(
            ticket_id=ticket.id,
            user_id=user.id,
            event_type="Назначение отдела",
            details=f"Заявка #{ticket.id} направлена в отдел «{department.name}»",
        )

        TicketService.change_status(ticket, "В обработке", user)
        db.session.commit()

        from app.services.notification_service import NotificationService
        if department.head_id and department.head_id != user.id:
            NotificationService.create_notification(
                user_id=department.head_id,
                message=f"В ваш отдел направлена заявка #{ticket.id}.",
                ticket_id=ticket.id,
            )

        if user.id != ticket.applicant_id:
            NotificationService.create_notification(
                user_id=ticket.applicant_id,
                message=f"Ваша заявка #{ticket.id} направлена в отдел «{department.name}».",
                ticket_id=ticket.id,
            )

        TicketService._emit_to_dashboards("ticket_updated", ticket)
        return True

    @staticmethod
    def _emit_to_dashboards(event_name, ticket, extra_data=None):
        rooms = set()
        user_id = ticket.applicant_id

        if ticket.status != "Решена":
            rooms.add(f"dashboard_user_{user_id}")
        else:
            rooms.add(f"dashboard_archive_{user_id}")

        if ticket.status != "Решена":
            for executor in ticket.executors:
                rooms.add(f"dashboard_executor_{executor.id}")

        # Классификаторы видят все активные заявки своего отдела и нераспределённые —
        # рассылаем им все незакрытые, а клиент сам отфильтрует по релевантности
        if ticket.status != "Решена":
            rooms.add("dashboard_classifier_all")

        if ticket.status != "Решена":
            rooms.add("dashboard_admin_all")

        if ticket.status == "Решена":
            for executor in ticket.executors:
                rooms.add(f"dashboard_archive_{executor.id}")

        if ticket.status != "Решена":
            for dept in ticket.departments:
                if dept.head_id:
                    rooms.add(f"dashboard_head_{dept.head_id}")

        ticket_dict = ticket.to_dict()
        data = {"ticket": ticket_dict, "changed_fields": extra_data or {}}

        for room in rooms:
            socketio.emit(event_name, data, room=room)
