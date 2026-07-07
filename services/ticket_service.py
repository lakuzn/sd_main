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
from app.services.notification_service import NotificationService
from app.services.log_service import LogService
from app.extensions import socketio, db
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
import os
from datetime import date, datetime

from app.utils.network import get_client_ip, resolve_hostname


class TicketService:

    @staticmethod
    def get_ticket(ticket_id):
        ticket = Ticket.query.get_or_404(ticket_id)
        return ticket

    @staticmethod
    def _recipients(ticket, exclude_id=None):
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
    def _notify(ticket, message, actor_id=None, important=False):
        from app.services.notification_service import NotificationService

        NotificationService.notify_many(
            TicketService._recipients(ticket, exclude_id=actor_id),
            message,
            ticket.id,
            important=important,
        )

    @staticmethod
    def mark_ticket_viewed(ticket_id, user_id):
        view = TicketView.query.filter_by(ticket_id=ticket_id, user_id=user_id).first()

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
        if user.role == "admin":
            return True

        if ticket.is_deleted:
            return False

        if user.id == ticket.applicant_id:
            return True

        if user in ticket.executors:
            return True

        if user.role == "classifier":
            return True

        if user.role in ["executor", "head"] and user.department_id:
            for dept in ticket.departments:
                if dept.id == user.department_id:
                    return True

        return False

    @staticmethod
    def delete_ticket(ticket_id, user):
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
            new_ticket.document_number = original.document_number
            new_ticket.classifier_id = user.id

        db.session.add(new_ticket)
        db.session.flush()

        new_ticket.categories = list(original.categories)

        if is_staff_clone:
            new_ticket.executors = list(original.executors)
            new_ticket.departments = list(original.departments)

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
                important=True,
            )

        return new_ticket

    @staticmethod
    def validate_ticket_data(desired_deadline):
        if desired_deadline and desired_deadline < date.today():
            return False, "Нельзя создать заявку с уже истёкшим сроком."
        return True, None

    @staticmethod
    def determine_applicant(current_user, on_behalf_of_id):
        if not on_behalf_of_id:
            return current_user.id, None

        allowed_roles = ["classifier", "executor", "head", "admin"]
        if current_user.role not in allowed_roles:
            return current_user.id, None

        target = User.query.get(on_behalf_of_id)
        if not target:
            return current_user.id, f"Пользователь с ID {on_behalf_of_id} не найден"

        return target.id, None

    @staticmethod
    def update_user_hostname(user):
        client_ip = get_client_ip()
        if not client_ip:
            return None

        host = resolve_hostname(client_ip)
        if host and host != user.host_name:
            user.host_name = host
            db.session.commit()
            return host
        return None

    @staticmethod
    def create_ticket(
        applicant_id,
        description,
        attachments=None,
        desired_deadline=None,
        host_name=None,
    ):
        try:
            is_valid, error = TicketService.validate_ticket_data(desired_deadline)
            if not is_valid:
                raise ValueError(error)

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
                details=f"Заявка #{ticket.id} зарегистрирована в системе",
            )

            db.session.commit()

            TicketService._emit_to_dashboards("ticket_created", ticket)

            NotificationService.create_notification(
                user_id=applicant_id,
                message=f"Ваша заявка #{ticket.id} успешно зарегистрирована в системе.",
                ticket_id=ticket.id,
            )

            return ticket

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Ошибка создания заявки: {e}")
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

        TicketService.mark_ticket_viewed(ticket.id, user.id)

        from app.services.notification_service import NotificationService

        if ticket.status == "Ожидает ответа" and old_status != "Ожидает ответа":
            NotificationService.create_notification(
                user_id=ticket.applicant_id,
                message=f"Исполнитель ожидает вашего ответа по заявке #{ticket.id}.",
                ticket_id=ticket.id,
            )
        elif (
            user.role == "user"
            and old_status == "Ожидает ответа"
            and ticket.status != "Ожидает ответа"
        ):
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

        TicketService._emit_to_dashboards(
            "ticket_updated",
            ticket,
            extra_data={"new_message": True},
        )

    @staticmethod
    def _update_ticket_status_after_message(ticket, user_role, user):
        new_status = None

        has_executors = len(ticket.executors) > 0

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
            important=True,
        )

        return True, ticket

    @staticmethod
    def _save_attachments(ticket_id, files, message_id=None, comment_id=None):

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
            .options(joinedload(Message.sender))
            .order_by(Message.created_at.asc())
            .all()
        )

        category_ids = [c.id for c in ticket.categories] if ticket.categories else []
        executor_ids = [c.id for c in ticket.executors] if ticket.executors else []
        department_ids = (
            [d.id for d in ticket.departments] if ticket.departments else []
        )

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
                .options(joinedload(InternalComment.author))
                .order_by(InternalComment.created_at.asc())
                .all()
            )
            context["logs"] = (
                ActivityLog.query.filter_by(ticket_id=ticket.id)
                .options(joinedload(ActivityLog.user))
                .order_by(ActivityLog.created_at.desc())
                .limit(50)
                .all()
            )

            context["categories"] = Category.query.all()
            context["departments"] = Department.query.all()

            context["executors"] = TicketService.get_assignable_executors(current_user)

        if current_user.role == "classifier":
            if ticket.status == "Новая":
                ticket.status = "В обработке"
                ticket.classifier_id = current_user.id
                db.session.commit()

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
                important=True,
            )

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

    EXECUTOR_ROLES = ["executor", "head", "classifier"]

    @staticmethod
    def _base_department_ids(user):
        ids = set()
        if user.department_id:
            ids.add(user.department_id)

        for dept in Department.query.filter_by(head_id=user.id).all():
            ids.add(dept.id)

        try:
            for dept in user.managed_departments:
                ids.add(dept.id)
        except Exception:
            db.session.rollback()

        return ids

    @staticmethod
    def get_assignable_executors(user):
        base_query = User.query.filter(
            User.role.in_(TicketService.EXECUTOR_ROLES),
            User.is_active.is_(True),
        )

        if user.role != "head":
            return base_query.order_by(User.full_name).all()

        all_departments = Department.query.all()
        subtree_ids = Department.resolve_subtree(
            all_departments, TicketService._base_department_ids(user)
        )
        if not subtree_ids:
            return []

        return (
            base_query.filter(User.department_id.in_(subtree_ids))
            .order_by(User.full_name)
            .all()
        )

    @staticmethod
    def setup_route_form(form, user=None):
        TicketService.setup_category_choices(form)
        TicketService.setup_executor_choices(form, user)
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
    def setup_executor_choices(form, user=None):
        if user is not None and user.role == "head":
            executors = TicketService.get_assignable_executors(user)
        else:
            executors = (
                User.query.filter(User.role.in_(TicketService.EXECUTOR_ROLES))
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
                important=True,
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
                if executor_ids:
                    ticket.departments = []
                executors_changed = True

            elif key == "department_ids":
                dept_ids = [v for v in value if isinstance(v, int)]
                ticket.departments = Department.query.filter(
                    Department.id.in_(dept_ids)
                ).all()
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

        if executors_changed:
            if ticket.executors:
                departments_set = set()
                for ex in ticket.executors:
                    if ex.department:
                        departments_set.add(ex.department)
                ticket.departments = list(departments_set)

                if ticket.status in ["Новая", "В обработке"]:
                    TicketService.change_status(ticket, "В работе", user)
            else:
                if ticket.departments and ticket.status in [
                    "В работе",
                    "Ожидает ответа",
                ]:
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

            if executors_changed:
                from app.services.notification_service import NotificationService

                added = {ex.id for ex in ticket.executors} - old_executor_ids
                for uid in added:
                    NotificationService.create_notification(
                        user_id=uid,
                        message=f"Вам назначена заявка #{ticket.id}.",
                        ticket_id=ticket.id,
                        important=True,
                    )

            return True
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при сохранении параметров: {e}")
            return False

    @staticmethod
    def take_in_work(ticket, user):
        if (
            ticket.status == "В обработке"
            and user.department in ticket.departments
            and not ticket.executors
        ):
            ticket.executors.append(user)

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
            important=True,
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
                important=True,
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
