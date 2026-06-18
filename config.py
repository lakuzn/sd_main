# Файл с настройками (который будет читать для нас .env)

import os
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()


class Config:
    # Поддерживаем оба написания: правильное SECRET_KEY и историческое
    # SERCET_KEY (с опечаткой) — чтобы старые .env продолжали работать.
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.environ.get("SERCET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    # Отключение лишней функции слежения за изменениями
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Максимальный размер загружаемого файла — 100 МБ
    # (запрос больше этого размера будет отклонён сервером)
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024

    # ======================================================================
    # Active Directory / LDAP
    # ----------------------------------------------------------------------
    # ВНИМАНИЕ: значения со словами CHANGE-ME / EXAMPLE — это ЗАГЛУШКИ.
    # Их нужно узнать у системного администратора и прописать в файле .env
    # (или в переменных окружения сервиса IIS). Здесь они стоят только для
    # того, чтобы приложение запускалось без падения.
    # ======================================================================

    # Адрес контроллера домена для LDAP. Можно указать НЕСКОЛЬКО адресов через
    # запятую — приложение будет использовать их как отказоустойчивый пул:
    # если один контроллер недоступен, ldap3 переключится на следующий.
    # Для обычного LDAP — порт 389, для защищённого LDAPS — порт 636 (рекомендуется).
    # <<< УЗНАТЬ: адрес(а) контроллеров домена >>>
    # Пример одного:    "ldaps://dc01..ru"
    # Пример нескольких: "ldaps://dc01..ru,ldaps://dc02..ru"
    AD_LDAP_SERVER = os.environ.get(
        "AD_LDAP_SERVER",
        "ldaps://srv01002.polyot.ru,ldaps://srv01005.polyot.ru,ldaps://srv01006.polyot.ru ",
    )

    # Использовать ли LDAPS (шифрование TLS). True — порт 636.
    AD_USE_SSL = os.environ.get("AD_USE_SSL", "true").lower() == "true"

    # NetBIOS-имя домена (короткое), используется в логине вида DOMAIN\user.
    # <<< УЗНАТЬ: например COMPANY >>>
    AD_DOMAIN = os.environ.get("AD_DOMAIN", "POLYOT")

    # Полное (FQDN) имя домена — для адресов почты/UPN по умолчанию.
    AD_DOMAIN_FQDN = os.environ.get(
        "AD_DOMAIN_FQDN", "srv01002.polyot.ru,srv01005.polyot.ru,srv01006.polyot.ru"
    )

    # Базовая ветка (Base DN), внутри которой искать пользователей.
    # <<< УЗНАТЬ: например DC=company,DC=local или OU=Сотрудники,DC=company,DC=local >>>
    AD_BASE_DN = os.environ.get(
        "AD_BASE_DN", "OU=Person,OU=Users,OU=Local,DC=Polyot,DC=ru"
    )

    # Сервисная учётная запись для ЧТЕНИЯ каталога (нужны только права чтения).
    # Формат логина: DOMAIN\учётка  (или UPN: учётка@company.local)
    AD_BIND_USER = os.environ.get("AD_BIND_USER", "POLYOT\srvc01014")
    AD_BIND_PASSWORD = os.environ.get("AD_BIND_PASSWORD", "W3j9Tg6Pze7LHt5")

    # Способ привязки к LDAP: "NTLM" (привычно для AD) или "SIMPLE" (обычно по LDAPS).
    AD_AUTH_METHOD = os.environ.get("AD_AUTH_METHOD", "SIMPLE")

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
    # AD_GROUP_ROLE_MAP = os.environ.get("AD_GROUP_ROLE_MAP", "")

    # Роль по умолчанию для новых пользователей, не попавших ни в одну группу.
    AD_DEFAULT_ROLE = os.environ.get("AD_DEFAULT_ROLE", "user")

    # ======================================================================
    # Аутентификация через Kerberos (Single Sign-On)
    # ======================================================================

    # Включить вход по Kerberos/Windows (SSO). На рабочем сервере — true,
    # на машине разработчика без домена false (тогда работает вход
    # по логину/паролю как раньше).
    KERBEROS_SSO_ENABLED = (
        os.environ.get("KERBEROS_SSO_ENABLED", "true").lower() == "true"
    )
