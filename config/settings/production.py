"""
config/settings/production.py
================================
Production overrides.

FIX: Changed database config to use DATABASE_URL (dj-database-url) instead of
     individual DB_NAME/DB_USER/etc. vars — matches what's in .env (NeonDB URL).
"""

from .base import *
import dj_database_url

DEBUG = False
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())

# ── FIX: Use DATABASE_URL just like development does ─────────
# Your .env has DATABASE_URL=postgresql://... (NeonDB).
# The old approach (individual DB_* vars) would crash since those
# vars don't exist in .env.
DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True,
    )
}

# ── HTTPS / Security headers ──────────────────────────────────
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", cast=Csv())
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# ── Sentry error tracking ─────────────────────────────────────
try:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(
        dsn=config("SENTRY_DSN", default=""),
        integrations=[
            DjangoIntegration(transaction_style="url"),
            CeleryIntegration(monitor_beat_tasks=True),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )
except Exception:
    pass  # Sentry optional — don't crash if SENTRY_DSN is blank

# ── Production logging ────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"},
    },
    "handlers": {
        "file": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs/error.log",
            "maxBytes": 1024 * 1024 * 10,
            "backupCount": 5,
            "formatter": "verbose",
        },
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console", "file"], "level": "WARNING"},
}
