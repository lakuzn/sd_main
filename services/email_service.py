import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from flask import current_app

from app.extensions import socketio


class EmailService:

    @staticmethod
    def is_enabled():
        return bool(current_app.config.get("MAIL_ENABLED", False))

    @staticmethod
    def _render_html(subject, message, ticket_url):
        path = os.path.join(
            current_app.root_path, "utils", "email_templates", "email.html.j2"
        )
        try:
            with open(path, encoding="utf-8") as f:
                template = f.read()
        except OSError:
            template = ""

        if not template.strip():
            return f"<p>{message}</p>"

        return current_app.jinja_env.from_string(template).render(
            subject=subject, message=message, ticket_url=ticket_url
        )

    @staticmethod
    def send_notification_email(recipient, subject, message, ticket_url=None):
        if not EmailService.is_enabled() or not recipient:
            return False

        app = current_app._get_current_object()
        html = EmailService._render_html(subject, message, ticket_url)
        socketio.start_background_task(
            EmailService._deliver, app, recipient, subject, message, html
        )
        return True

    @staticmethod
    def _deliver(app, recipient, subject, message, html):
        with app.app_context():
            cfg = app.config
            sender = cfg.get("MAIL_DEFAULT_SENDER") or "servicedesk@localhost"

            try:
                email_msg = EmailMessage()
                email_msg["Subject"] = subject
                email_msg["From"] = formataddr(("ServiceDesk", sender))
                email_msg["To"] = recipient
                email_msg.set_content(message)  # текстовая версия (fallback)
                email_msg.add_alternative(html, subtype="html")

                server = cfg.get("MAIL_SERVER", "localhost")
                port = int(cfg.get("MAIL_PORT", 25))
                timeout = int(cfg.get("MAIL_TIMEOUT", 10))
                username = cfg.get("MAIL_USERNAME")
                password = cfg.get("MAIL_PASSWORD")

                if cfg.get("MAIL_USE_SSL"):
                    context = ssl.create_default_context()
                    smtp = smtplib.SMTP_SSL(
                        server, port, timeout=timeout, context=context
                    )
                else:
                    smtp = smtplib.SMTP(server, port, timeout=timeout)

                with smtp:
                    if cfg.get("MAIL_USE_TLS"):
                        smtp.starttls(context=ssl.create_default_context())
                    if username:
                        smtp.login(username, password or "")
                    smtp.send_message(email_msg)

                app.logger.info("Уведомление отправлено на почту %s", recipient)
            except Exception as exc:  # noqa: BLE001 — сбой почты не должен ронять заявку
                app.logger.error(
                    "Не удалось отправить письмо на %s: %s", recipient, exc
                )
