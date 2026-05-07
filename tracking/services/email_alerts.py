from __future__ import annotations

import base64
import json
import logging
import smtplib
import ssl
from email.message import EmailMessage
from urllib import parse, request as urlrequest

from django.conf import settings
from django.core.cache import cache

from tracking.models import IntentoAccesoPortal, PublicAlertRecipient

logger = logging.getLogger(__name__)


def _split_recipients(value: str) -> list[str]:
    # Prefer recipients configured in DB (active), fallback to env list
    db_recipients = list(
        PublicAlertRecipient.objects.filter(active=True).values_list("email", flat=True)
    )
    if db_recipients:
        return [r for r in db_recipients]
    return [recipient.strip() for recipient in (value or "").split(",") if recipient.strip()]


def _build_oauth_access_token() -> str:
    client_id = getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", "")
    client_secret = getattr(settings, "GOOGLE_OAUTH_CLIENT_SECRET", "")
    refresh_token = getattr(settings, "GOOGLE_OAUTH_REFRESH_TOKEN", "")
    token_url = getattr(settings, "GOOGLE_OAUTH_TOKEN_URL", "https://oauth2.googleapis.com/token")

    if not (client_id and client_secret and refresh_token):
        raise ValueError("Faltan credenciales OAuth de Google para enviar alertas por email.")

    payload = parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
    ).encode("utf-8")

    req = urlrequest.Request(token_url, data=payload, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urlrequest.urlopen(req, timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))

    access_token = data.get("access_token")
    if not access_token:
        raise ValueError("Google no devolvio un access_token valido para enviar alertas.")
    return access_token


def _build_xoauth2_string(username: str, access_token: str) -> str:
    auth_string = f"user={username}\1auth=Bearer {access_token}\1\1"
    return base64.b64encode(auth_string.encode("utf-8")).decode("ascii")


def _smtp_connect():
    host = getattr(settings, "EMAIL_HOST", "smtp.gmail.com")
    port = int(getattr(settings, "EMAIL_PORT", 587))
    use_ssl = bool(getattr(settings, "EMAIL_USE_SSL", False))
    use_tls = bool(getattr(settings, "EMAIL_USE_TLS", True))

    if use_ssl:
        return smtplib.SMTP_SSL(host=host, port=port, timeout=20)

    connection = smtplib.SMTP(host=host, port=port, timeout=20)
    if use_tls:
        context = ssl.create_default_context()
        connection.starttls(context=context)
    return connection


def send_public_access_alert(*, intento: IntentoAccesoPortal) -> bool:
    if intento.motivo != IntentoAccesoPortal.Motivo.HOJA_INEXISTENTE:
        return False

    recipients = _split_recipients(getattr(settings, "PUBLIC_ALERT_RECIPIENTS", ""))
    sender = getattr(settings, "EMAIL_FROM", "") or getattr(settings, "EMAIL_HOST_USER", "")
    username = getattr(settings, "EMAIL_HOST_USER", "")

    if not recipients or not sender or not username:
        logger.info("Alerta de acceso omitida por falta de configuracion de correo.")
        return False

    cache_key = f"public-access-alert:{intento.canal}:{intento.oid}"
    if cache.get(cache_key):
        return False

    subject = f"Alerta: intento de acceso a hoja inexistente {intento.oid}"
    body = (
        f"Se registro un intento de acceso a un link publico de conformados.\n\n"
        f"Canal: {intento.canal}\n"
        f"OID: {intento.oid}\n"
        f"Fecha: {intento.fecha_evento:%d/%m/%Y %H:%M:%S}\n"
        f"IP: {intento.ip_address or '-'}\n"
        f"Ruta: {intento.path or '-'}\n"
        f"Detalle: {intento.detalle or '-'}\n"
    )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message.set_content(body)

    access_token = _build_oauth_access_token()
    xoauth2 = _build_xoauth2_string(username, access_token)

    connection = _smtp_connect()
    try:
        connection.ehlo()
        if not getattr(settings, "EMAIL_USE_SSL", False):
            connection.ehlo()
        connection.docmd("AUTH", f"XOAUTH2 {xoauth2}")
        connection.send_message(message)
    finally:
        connection.quit()

    cache.set(cache_key, True, 300)
    return True