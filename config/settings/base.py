import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-change-me")

ALLOWED_HOSTS = [
    host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "tracking",
]

MIDDLEWARE = [
    "config.middleware.RequestLoggingMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "tracking.context_processors.empresa_theme",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Cordoba"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/panel/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

EVIDENCIA_MAX_IMAGE_SIZE_MB = int(os.getenv("EVIDENCIA_MAX_IMAGE_SIZE_MB", "8"))
EVIDENCIA_MAX_PDF_SIZE_MB = int(os.getenv("EVIDENCIA_MAX_PDF_SIZE_MB", "15"))
EVIDENCIA_RATE_LIMIT_COUNT = int(os.getenv("EVIDENCIA_RATE_LIMIT_COUNT", "10"))
EVIDENCIA_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("EVIDENCIA_RATE_LIMIT_WINDOW_SECONDS", "60"))
NO_ENTREGADO_RATE_LIMIT_COUNT = int(os.getenv("NO_ENTREGADO_RATE_LIMIT_COUNT", "6"))
NO_ENTREGADO_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("NO_ENTREGADO_RATE_LIMIT_WINDOW_SECONDS", "600"))
PUBLIC_LINK_INVALID_RATE_LIMIT_COUNT = int(os.getenv("PUBLIC_LINK_INVALID_RATE_LIMIT_COUNT", "5"))
PUBLIC_LINK_INVALID_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("PUBLIC_LINK_INVALID_RATE_LIMIT_WINDOW_SECONDS", "600"))

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "1") == "1"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "0") == "1"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", EMAIL_HOST_USER)
PUBLIC_ALERT_RECIPIENTS = os.getenv("PUBLIC_ALERT_RECIPIENTS", "")

GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
GOOGLE_OAUTH_REFRESH_TOKEN = os.getenv("GOOGLE_OAUTH_REFRESH_TOKEN", "")
GOOGLE_OAUTH_TOKEN_URL = os.getenv("GOOGLE_OAUTH_TOKEN_URL", "https://oauth2.googleapis.com/token")
