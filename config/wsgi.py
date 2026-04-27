import logging
import os
import sys
import traceback

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.development"),
)

# ---------------------------------------------------------------------------
# Bootstrap logging early so any import-time crash is captured before Django's
# logging machinery is fully initialised.
# ---------------------------------------------------------------------------
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="[WSGI] %(asctime)s %(levelname)s %(name)s: %(message)s",
)
_wsgi_logger = logging.getLogger("config.wsgi")

_wsgi_logger.info("WSGI startup — DJANGO_SETTINGS_MODULE=%s", os.environ.get("DJANGO_SETTINGS_MODULE"))

try:
    from django.core.wsgi import get_wsgi_application
    from django.core.management import call_command

    _django_app = get_wsgi_application()
    if os.getenv("DJANGO_SETTINGS_MODULE", "").endswith("railway") and os.getenv("DJANGO_RUN_STARTUP_COMMANDS", "1") == "1":
        _wsgi_logger.info("Running Railway startup commands: migrate + ensure_initial_admin")
        call_command("migrate", interactive=False, verbosity=1)
        call_command("ensure_initial_admin", verbosity=1)
        _wsgi_logger.info("Railway startup commands completed.")
    _wsgi_logger.info("Django WSGI application loaded successfully.")
except Exception:  # noqa: BLE001
    _wsgi_logger.critical(
        "FATAL: Django failed to initialise during WSGI startup.\n%s",
        traceback.format_exc(),
    )
    raise


def application(environ, start_response):  # type: ignore[override]
    """Thin wrapper around the Django WSGI app that logs unhandled exceptions."""
    try:
        return _django_app(environ, start_response)
    except Exception:  # noqa: BLE001
        _wsgi_logger.error(
            "Unhandled exception in WSGI application:\n%s",
            traceback.format_exc(),
        )
        raise
