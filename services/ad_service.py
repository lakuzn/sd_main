"""Интеграция с Active Directory (выгрузка пользователей по LDAP).

Сюда вынесена вся работа с каталогом AD. Библиотека ldap3 импортируется
ЛЕНИВО внутри методов — так приложение спокойно запускается даже там, где
ldap3 не установлен (например, на машине разработчика без домена), а ошибка
возникнет только при реальной попытке синхронизации.

Самый важный метод — AdService.sync_users(): он подключается к контроллеру
домена, читает всех пользователей и сохраняет/обновляет их в нашей базе.
Его вызывает как первичная выгрузка, так и ночной скрипт sync_ad_users.py.
"""

from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models import User, Department


class AdService:

    # --- Атрибуты AD, которые мы запрашиваем у каталога ---
    ATTRIBUTES = [
        "sAMAccountName",     # логин (username)
        "userPrincipalName",  # логин вида user@company.local
        "displayName",        # ФИО для отображения
        "cn",                 # запасной вариант ФИО
        "givenName",          # имя
        "sn",                 # фамилия
        "mail",               # почта
        "telephoneNumber",    # телефон
        "title",              # должность
        "department",         # отдел (строка)
        "userAccountControl", # битовая маска (узнаём, отключена ли учётка)
        "objectGUID",         # стабильный идентификатор учётки
        "memberOf",           # группы (для назначения ролей)
    ]

    # ------------------------------------------------------------------ #
    #  Подключение к каталогу
    # ------------------------------------------------------------------ #
    @staticmethod
    def _get_connection():
        """Создаёт и возвращает подключение к LDAP (ldap3.Connection)."""
        # Ленивый импорт: ldap3 нужен только в момент реальной синхронизации
        from ldap3 import Server, Connection, ALL, NTLM, SIMPLE

        cfg = current_app.config
        server = Server(
            cfg["AD_LDAP_SERVER"],
            use_ssl=cfg["AD_USE_SSL"],
            get_info=ALL,
        )

        auth = NTLM if cfg.get("AD_AUTH_METHOD", "NTLM").upper() == "NTLM" else SIMPLE

        conn = Connection(
            server,
            user=cfg["AD_BIND_USER"],
            password=cfg["AD_BIND_PASSWORD"],
            authentication=auth,
            auto_bind=True,
        )
        return conn

    # ------------------------------------------------------------------ #
    #  Чтение пользователей из AD
    # ------------------------------------------------------------------ #
    @staticmethod
    def fetch_users():
        """Возвращает список пользователей из AD в виде словарей."""
        from ldap3 import SUBTREE

        cfg = current_app.config
        conn = AdService._get_connection()

        users = []
        # Постраничный поиск (paged_search) — чтобы не упереться в лимит
        # сервера (обычно AD отдаёт максимум 1000 записей за раз).
        entries = conn.extend.standard.paged_search(
            search_base=cfg["AD_BASE_DN"],
            search_filter=cfg["AD_USER_FILTER"],
            search_scope=SUBTREE,
            attributes=AdService.ATTRIBUTES,
            paged_size=500,
            generator=True,
        )

        for entry in entries:
            if entry.get("type") != "searchResEntry":
                continue
            attrs = entry.get("attributes", {})
            parsed = AdService._parse_entry(attrs)
            if parsed:
                users.append(parsed)

        conn.unbind()
        return users

    @staticmethod
    def _parse_entry(attrs):
        """Превращает «сырые» атрибуты LDAP в удобный словарь."""

        def one(value):
            # LDAP-атрибуты часто приходят списками — берём первый элемент
            if isinstance(value, (list, tuple)):
                return value[0] if value else None
            return value

        username = one(attrs.get("sAMAccountName"))
        if not username:
            return None  # без логина учётка нам бесполезна
        username = str(username).strip().lower()

        guid = one(attrs.get("objectGUID"))
        guid = str(guid).strip("{}").lower() if guid else None

        cfg = current_app.config
        mail = one(attrs.get("mail"))
        if not mail:
            # запасная почта вида login@company.local
            mail = f"{username}@{cfg['AD_DOMAIN_FQDN']}"

        full_name = (
            one(attrs.get("displayName"))
            or one(attrs.get("cn"))
            or " ".join(
                p for p in [one(attrs.get("givenName")), one(attrs.get("sn"))] if p
            )
            or username
        )

        # userAccountControl: бит 0x2 (ACCOUNTDISABLE) — учётка отключена
        try:
            uac = int(one(attrs.get("userAccountControl")) or 0)
        except (TypeError, ValueError):
            uac = 0
        is_disabled = bool(uac & 0x2)

        member_of = attrs.get("memberOf") or []
        if not isinstance(member_of, (list, tuple)):
            member_of = [member_of]

        return {
            "username": username,
            "ad_guid": guid,
            "email": str(mail).strip().lower(),
            "full_name": str(full_name).strip(),
            "phone": (one(attrs.get("telephoneNumber")) or None),
            "position": (one(attrs.get("title")) or None),
            "department": (one(attrs.get("department")) or None),
            "is_active": not is_disabled,
            "member_of": [str(g) for g in member_of],
        }

    # ------------------------------------------------------------------ #
    #  Вспомогательное: роли по группам, отделы
    # ------------------------------------------------------------------ #
    @staticmethod
    def _role_from_groups(member_of):
        """Определяет роль по членству в группах AD (по карте из конфига)."""
        raw_map = current_app.config.get("AD_GROUP_ROLE_MAP", "") or ""
        if not raw_map:
            return None

        # Карта вида "Group-A=classifier;Group-B=executor"
        mapping = {}
        for pair in raw_map.split(";"):
            if "=" in pair:
                cn, role = pair.split("=", 1)
                mapping[cn.strip().lower()] = role.strip()

        # В memberOf приходят полные DN: "CN=Group-A,OU=...,DC=...".
        # Берём CN (первый компонент) и сравниваем с картой.
        for dn in member_of:
            cn = dn.split(",")[0].replace("CN=", "").replace("cn=", "").strip().lower()
            if cn in mapping:
                return mapping[cn]
        return None

    @staticmethod
    def _get_or_create_department(name):
        """Находит отдел по имени или создаёт новый.

        Сопоставление по точному имени: AD отдаёт название отдела стабильной
        строкой, а регистронезависимое сравнение через SQL lower() ненадёжно
        для кириллицы (зависит от СУБД).
        """
        name = (name or "").strip()
        if not name:
            return None
        dept = Department.query.filter_by(name=name).first()
        if not dept:
            dept = Department(name=name)
            db.session.add(dept)
            db.session.flush()
        return dept

    # ------------------------------------------------------------------ #
    #  Главный метод: синхронизация
    # ------------------------------------------------------------------ #
    @staticmethod
    def sync_users(deactivate_missing=True):
        """Выгружает пользователей из AD и сохраняет/обновляет их в нашей БД.

        Логика:
        - находим существующего пользователя по ad_guid (надёжнее всего),
          иначе по username, иначе по email;
        - новых создаём, существующих обновляем;
        - роли существующих пользователей НЕ перезаписываем (их могли
          назначить вручную в приложении); роль ставим только новым;
        - отключённых/исчезнувших из AD помечаем неактивными, но не удаляем.

        Возвращает словарь со статистикой.
        """
        ad_users = AdService.fetch_users()

        default_role = current_app.config.get("AD_DEFAULT_ROLE", "user")
        now = datetime.now()

        stats = {"total": len(ad_users), "created": 0, "updated": 0, "deactivated": 0}
        seen_guids = set()

        for data in ad_users:
            if data["ad_guid"]:
                seen_guids.add(data["ad_guid"])

            user = None
            if data["ad_guid"]:
                user = User.query.filter_by(ad_guid=data["ad_guid"]).first()
            if not user and data["username"]:
                user = User.query.filter_by(username=data["username"]).first()
            if not user and data["email"]:
                user = User.query.filter_by(email=data["email"]).first()

            dept = AdService._get_or_create_department(data["department"])

            if user is None:
                # Новый пользователь
                role = AdService._role_from_groups(data["member_of"]) or default_role
                user = User(
                    username=data["username"],
                    ad_guid=data["ad_guid"],
                    email=data["email"],
                    full_name=data["full_name"],
                    phone=data["phone"],
                    position=data["position"],
                    role=role,
                    department=dept,
                    is_active=data["is_active"],
                    last_sync_at=now,
                )
                db.session.add(user)
                stats["created"] += 1
            else:
                # Обновляем данные (роль не трогаем — могла быть выставлена вручную)
                user.username = data["username"] or user.username
                user.ad_guid = data["ad_guid"] or user.ad_guid
                user.email = data["email"] or user.email
                user.full_name = data["full_name"] or user.full_name
                user.phone = data["phone"]
                user.position = data["position"]
                if dept:
                    user.department = dept
                user.is_active = data["is_active"]
                user.last_sync_at = now
                stats["updated"] += 1

        # Учётки, которые раньше пришли из AD (есть ad_guid), но в этой
        # выгрузке отсутствуют — помечаем неактивными (уволены/удалены).
        if deactivate_missing and seen_guids:
            stale = User.query.filter(
                User.ad_guid.isnot(None),
                ~User.ad_guid.in_(seen_guids),
                User.is_active.is_(True),
            ).all()
            for u in stale:
                u.is_active = False
                u.last_sync_at = now
                stats["deactivated"] += 1

        db.session.commit()
        return stats
