# Экспортируем все модели, чтобы можно было писать from app.models import User, Ticket, ...

from .user import User
from .ticket import Ticket
from .category import Category
from .message import Message
from .attachment import Attachment
from .activity_log import ActivityLog
from .knowledge_article import KnowledgeArticle
from .department import Department
from .internal_comment import InternalComment
from .notification import Notification
from .ticket_view import TicketView


__all__ = [
    "User",
    "Ticket",
    "Category",
    "Attachment",
    "Message",
    "ActivityLog",
    "KnowledgeArticle",
    "Department",
    "InternalComment",
    "Notification",
    "TicketView",
]
