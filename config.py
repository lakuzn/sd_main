import os
from dotenv import load_dotenv
load_dotenv()
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.environ.get("SERCET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": int(os.environ.get("DB_POOL_RECYCLE", "300")),
        "pool_size": int(os.environ.get("DB_POOL_SIZE", "5")),
        "max_overflow": int(os.environ.get("DB_MAX_OVERFLOW", "10")),
    }

    REDIS_URL = os.environ.get("REDIS_URL")

    MAX_CONTENT_LENGTH = 100 * 1024 * 1024

    AD_LDAP_SERVER = os.environ.get(
        "AD_LDAP_SERVER",
        "ldaps://srv01002.polyot.ru,ldaps://srv01005.polyot.ru,ldaps://srv01006.polyot.ru ",
    )

    AD_USE_SSL = os.environ.get("AD_USE_SSL", "true").lower() == "true"

    AD_DOMAIN = os.environ.get("AD_DOMAIN", "POLYOT")

    AD_DOMAIN_FQDN = os.environ.get(
        "AD_DOMAIN_FQDN", "srv01002.polyot.ru,srv01005.polyot.ru,srv01006.polyot.ru"
    )

    AD_BASE_DN = os.environ.get(
        "AD_BASE_DN", "OU=Person,OU=Users,OU=Local,DC=Polyot,DC=ru"
    )

    AD_BIND_USER = os.environ.get("AD_BIND_USER", "POLYOT\\CHANGE-ME")
    AD_BIND_PASSWORD = os.environ.get("AD_BIND_PASSWORD", "CHANGE-ME")

    AD_AUTH_METHOD = os.environ.get("AD_AUTH_METHOD", "SIMPLE")

    AD_USER_FILTER = os.environ.get(
        "AD_USER_FILTER",
        "(&(objectCategory=person)(objectClass=user))",
    )

    AD_DEFAULT_ROLE = os.environ.get("AD_DEFAULT_ROLE", "user")

    KERBEROS_SSO_ENABLED = (
        os.environ.get("KERBEROS_SSO_ENABLED", "true").lower() == "true"
    )
