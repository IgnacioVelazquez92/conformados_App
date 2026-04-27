import logging
import os

from .production import *  # noqa: F401,F403

# ---------------------------------------------------------------------------
# Core toggles
# ---------------------------------------------------------------------------
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", ".up.railway.app,localhost,127.0.0.1").split(",")
    if host.strip()
]

RAILWAY_PUBLIC_DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]
if RAILWAY_PUBLIC_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RAILWAY_PUBLIC_DOMAIN}")

# ---------------------------------------------------------------------------
# Structured logging — emit everything to stdout so Railway captures it.
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} {name} {process:d} {thread:d} | {message}",
            "style": "{",
        },
        "simple": {
            "format": "{asctime} {levelname} {name} | {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG" if DEBUG else "INFO",
    },
    "loggers": {
        # Our own code — always DEBUG so we see every request/exception.
        "config": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "tracking": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        # Django internals — INFO in production, DEBUG when DEBUG=1.
        "django": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.db.backends": {
            # Set to DEBUG only when explicitly requested to avoid log spam.
            "handlers": ["console"],
            "level": "DEBUG" if os.getenv("DJANGO_LOG_SQL", "0") == "1" else "WARNING",
            "propagate": False,
        },
    },
}

# ---------------------------------------------------------------------------
# Startup diagnostics — logged once when settings are first imported.
# ---------------------------------------------------------------------------
_startup_logger = logging.getLogger("config.railway")
_startup_logger.info("=== Railway settings loaded ===")
_startup_logger.info("DEBUG=%s", DEBUG)
_startup_logger.info("ALLOWED_HOSTS=%s", ALLOWED_HOSTS)
_startup_logger.info("CSRF_TRUSTED_ORIGINS=%s", CSRF_TRUSTED_ORIGINS)
_startup_logger.info("RAILWAY_PUBLIC_DOMAIN=%s", RAILWAY_PUBLIC_DOMAIN or "(not set)")
_startup_logger.info("DATABASE_URL present=%s", bool(os.getenv("DATABASE_URL")))
_startup_logger.info(
    "S3 bucket=%s  endpoint=%s",
    os.getenv("AWS_STORAGE_BUCKET_NAME") or os.getenv("BUCKET_NAME") or "(not set)",
    os.getenv("AWS_S3_ENDPOINT_URL") or os.getenv("BUCKET_ENDPOINT") or "(not set)",
)


def _check_db_connection() -> None:
    """Verify the database is reachable at startup and log the outcome."""
    try:
        from django.db import connection  # noqa: PLC0415

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        _startup_logger.info("Database connectivity check: OK")
    except Exception as exc:  # noqa: BLE001
        _startup_logger.error("Database connectivity check: FAILED — %s", exc)


# Run the DB check after Django's app registry is ready (AppConfig.ready would
# be cleaner, but this fires early enough to surface connection errors in logs).
try:
    import django  # noqa: PLC0415

    if django.apps.registry.apps.ready:
        _check_db_connection()
except Exception:  # noqa: BLE001
    pass  # Apps not ready yet; the check will be skipped silently.

