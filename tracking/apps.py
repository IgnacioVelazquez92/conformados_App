import logging

from django.apps import AppConfig

logger = logging.getLogger("config.railway")


class TrackingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tracking"

    def ready(self) -> None:
        """Run startup diagnostics once the app registry is fully loaded."""
        import os  # noqa: PLC0415

        # Diagnostic only. Keep disabled by default because ready() also runs
        # during commands like collectstatic and migrations.
        if os.getenv("DJANGO_SETTINGS_MODULE", "").endswith("railway") and os.getenv("RAILWAY_CHECK_DB_ON_READY", "0") == "1":
            self._check_db_connection()

    @staticmethod
    def _check_db_connection() -> None:
        """Verify the database is reachable and log the result."""
        try:
            from django.db import connection  # noqa: PLC0415

            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            logger.info("Database connectivity check (AppConfig.ready): OK")
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Database connectivity check (AppConfig.ready): FAILED — %s",
                exc,
                exc_info=True,
            )
