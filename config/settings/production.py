"""
config/settings/production.py
================================
Production overrides. Set via:
  DJANGO_SETTINGS_MODULE=config.settings.production
"""
from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration

DEBUG = False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# ── Production Database — persistent connections for speed ────
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     config('DB_NAME'),
        'USER':     config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST':     config('DB_HOST'),
        'PORT':     config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 60,              # Reuse DB connections 60s
        'OPTIONS': {
            'connect_timeout': 10,
            'sslmode': 'require',         # Force SSL
        },
    }
}

# ── HTTPS / Security headers ──────────────────────────────────
SECURE_SSL_REDIRECT                = True
SECURE_HSTS_SECONDS                = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS     = True
SECURE_HSTS_PRELOAD                = True
SECURE_PROXY_SSL_HEADER            = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE              = True
CSRF_COOKIE_SECURE                 = True
CSRF_TRUSTED_ORIGINS               = config('CSRF_TRUSTED_ORIGINS', cast=Csv())
X_FRAME_OPTIONS                    = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF        = True
SECURE_BROWSER_XSS_FILTER          = True

# ── Sentry error tracking ─────────────────────────────────────
sentry_sdk.init(
    dsn=config('SENTRY_DSN', default=''),
    integrations=[
        DjangoIntegration(transaction_style='url'),
        CeleryIntegration(monitor_beat_tasks=True),
        RedisIntegration(),
    ],
    traces_sample_rate=0.1,
    send_default_pii=False,
)

# ── Production logging ────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '{levelname} {asctime} {module} {message}', 'style': '{'},
    },
    'handlers': {
        'file':    {'level': 'WARNING', 'class': 'logging.handlers.RotatingFileHandler',
                    'filename': BASE_DIR / 'logs/error.log',
                    'maxBytes': 1024*1024*10, 'backupCount': 5, 'formatter': 'verbose'},
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
    },
    'root': {'handlers': ['console', 'file'], 'level': 'WARNING'},
}
