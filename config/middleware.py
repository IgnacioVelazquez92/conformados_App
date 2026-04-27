"""
config/middleware.py
--------------------
Diagnostic middleware for Railway deployments.

Logs every request/response cycle and emits a full stack trace for any
unhandled exception that would otherwise produce a silent HTTP 500.
"""

from __future__ import annotations

import logging
import time
import traceback

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("config.middleware")


class RequestLoggingMiddleware:
    """Log every request with timing, and capture 500-level errors with full tracebacks."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start = time.monotonic()

        logger.debug(
            "→ %s %s  host=%s  content_type=%s",
            request.method,
            request.get_full_path(),
            request.get_host(),
            request.content_type,
        )

        try:
            response = self.get_response(request)
        except Exception:  # noqa: BLE001
            elapsed = (time.monotonic() - start) * 1000
            logger.error(
                "UNHANDLED EXCEPTION  %s %s  (%.1f ms)\n%s",
                request.method,
                request.get_full_path(),
                elapsed,
                traceback.format_exc(),
            )
            raise

        elapsed = (time.monotonic() - start) * 1000
        level = logging.WARNING if response.status_code >= 400 else logging.DEBUG

        logger.log(
            level,
            "← %s  %s %s  (%.1f ms)",
            response.status_code,
            request.method,
            request.get_full_path(),
            elapsed,
        )

        if response.status_code >= 500:
            logger.error(
                "HTTP 500 on %s %s — check ALLOWED_HOSTS, DB connection, and middleware stack.",
                request.method,
                request.get_full_path(),
            )

        return response

    def process_exception(self, request: HttpRequest, exception: Exception) -> None:  # type: ignore[return]
        """Called by Django for exceptions raised inside view functions."""
        logger.error(
            "VIEW EXCEPTION  %s %s\n%s",
            request.method,
            request.get_full_path(),
            traceback.format_exc(),
        )
        # Return None so Django's default exception handling continues.
        return None
