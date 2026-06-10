# Файл с настройками (который будет читать для нас .env)

import os
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SERCET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    # Отключение лишней функции слежения за изменениями
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ======================================================================
    # Active Directory / LDAP
    # ----------------------------------------------------------------------
    # ВНИМАНИЕ: значения со словами CHANGE-ME / EXAMPLE — это ЗАГЛУШКИ.
    # Их нужно узнать у системного администратора и прописать в файле .env
    # (или в переменных окружения сервиса IIS). Здесь они стоят только для
    # того, чтобы приложение запускалось без падения.
    # ======================================================================

    # Адрес контроллера домена для LDAP. Для обычного LDAP — порт 389,
    # для защищённого LDAPS — порт 636 (рекомендуется).
    # <<< УЗНАТЬ: имя/адрес контроллера домена, например dc01.company.local >>>
    AD_LDAP_SERVER = os.environ.get(
        "AD_LDAP_SERVER", "ldap://CHANGE-ME-dc01.example.local"
    )

    # Использовать ли LDAPS (шифрование TLS). True — порт 636.
    AD_USE_SSL = os.environ.get("AD_USE_SSL", "false").lower() == "true"

    # NetBIOS-имя домена (короткое), используется в логине вида DOMAIN\user.
    # <<< УЗНАТЬ: например COMPANY >>>
    AD_DOMAIN = os.environ.get("AD_DOMAIN", "EXAMPLE")

    # Полное (FQDN) имя домена — для адресов почты/UPN по умолчанию.
    # <<< УЗНАТЬ: например company.local >>>
    AD_DOMAIN_FQDN = os.environ.get("AD_DOMAIN_FQDN", "example.local")

    # Базовая ветка (Base DN), внутри которой искать пользователей.
    # <<< УЗНАТЬ: например DC=company,DC=local или OU=Сотрудники,DC=company,DC=local >>>
    AD_BASE_DN = os.environ.get("AD_BASE_DN", "DC=example,DC=local")

    # Сервисная учётная запись для ЧТЕНИЯ каталога (нужны только права чтения).
    # Формат логина: DOMAIN\учётка  (или UPN: учётка@company.local)
    # <<< УЗНАТЬ: логин и пароль сервисной учётки только-для-чтения >>>
    AD_BIND_USER = os.environ.get("AD_BIND_USER", "EXAMPLE\\svc-servicedesk-read")
    AD_BIND_PASSWORD = os.environ.get("AD_BIND_PASSWORD", "CHANGE-ME")

    # Способ привязки к LDAP: "NTLM" (привычно для AD) или "SIMPLE" (обычно по LDAPS).
    AD_AUTH_METHOD = os.environ.get("AD_AUTH_METHOD", "NTLM")

    # LDAP-фильтр для выборки пользователей.
    # По умолчанию — все учётные записи людей (включая отключённые: их мы
    # пометим как неактивных, но не удалим, чтобы не потерять связи с заявками).
    AD_USER_FILTER = os.environ.get(
        "AD_USER_FILTER",
        "(&(objectCategory=person)(objectClass=user))",
    )

    # Сопоставление групп AD ролям приложения (необязательно).
    # Формат: "CN_группы=роль;CN_группы=роль"
    # Пример: "ServiceDesk-Classifiers=classifier;ServiceDesk-Executors=executor"
    # <<< УЗНАТЬ: точные имена (CN) групп безопасности AD >>>
    AD_GROUP_ROLE_MAP = os.environ.get("AD_GROUP_ROLE_MAP", "")

    # Роль по умолчанию для новых пользователей, не попавших ни в одну группу.
    AD_DEFAULT_ROLE = os.environ.get("AD_DEFAULT_ROLE", "user")

    # ======================================================================
    # Аутентификация через Kerberos (Single Sign-On)
    # ----------------------------------------------------------------------
    # Сам Kerberos выполняет IIS (Windows Authentication / Negotiate). Приложение
    # лишь доверяет уже аутентифицированному имени пользователя, которое IIS
    # передаёт в переменной окружения REMOTE_USER (вида DOMAIN\user или user@FQDN).
    # ======================================================================

    # Включить вход по Kerberos/Windows (SSO). На рабочем сервере IIS — true,
    # на машине разработчика без домена оставьте false (тогда работает вход
    # по логину/паролю как раньше).
    KERBEROS_SSO_ENABLED = (
        os.environ.get("KERBEROS_SSO_ENABLED", "false").lower() == "true"
    )
