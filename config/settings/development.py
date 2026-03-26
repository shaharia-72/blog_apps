"""
config/settings/development.py
================================
Development overrides. Set via:
  DJANGO_SETTINGS_MODULE=config.settings.development
"""
from .base import *
import dj_database_url

DEBUG = True
ALLOWED_HOSTS = ['*']

USE_POSTGRES = config("USE_POSTGRES", default=False, cast=bool)

if USE_POSTGRES:
    DATABASES = {
        "default": dj_database_url.config(
            default=config("DATABASE_URL", default="postgresql://postgres:postgres@localhost:5432/blog_dev"),
            conn_max_age=600,
            ssl_require=False,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# Print emails to console in dev — no email provider needed
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable throttling so you can test APIs freely
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]

# Show all SQL in terminal
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'loggers': {
        'django.db.backends': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
        'apps':               {'handlers': ['console'], 'level': 'DEBUG'},
        'core':               {'handlers': ['console'], 'level': 'DEBUG'},
    },
}
