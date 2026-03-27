"""
config/settings/development.py
================================
Development overrides.

FIXES:
  1. Added STATICFILES_STORAGE override — CompressedManifestStaticFilesStorage
     breaks in DEBUG=True mode. Use the simple storage in dev.
  2. Added note about USE_POSTGRES — set this in .env to use NeonDB.
"""

from .base import *
import dj_database_url

DEBUG = True
ALLOWED_HOSTS = ["*"]

# ── Database ──────────────────────────────────────────────────
# Set USE_POSTGRES=True in your .env file to use NeonDB (or any Postgres).
# Without it, Django uses SQLite — migrations won't touch your real DB.
USE_POSTGRES = config("USE_POSTGRES", default=False, cast=bool)

if USE_POSTGRES:
    DATABASES = {
        "default": dj_database_url.config(
            default=config("DATABASE_URL"),
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ── FIX: Use simple static storage in dev ─────────────────────
# CompressedManifestStaticFilesStorage (set in base.py) requires
# collectstatic to have been run and breaks in DEBUG=True mode.
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# ── Email: print to console ────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ── Disable DRF throttling so you can test APIs freely ────────
# NOTE: django-ratelimit on contact/subscribe views still works.
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# ── Show SQL queries in terminal for debugging ─────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "apps": {"handlers": ["console"], "level": "DEBUG"},
        "core": {"handlers": ["console"], "level": "DEBUG"},
    },
}
