"""
config/settings/development.py
================================
Development overrides. Set via:
  DJANGO_SETTINGS_MODULE=config.settings.development
"""
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     config('DB_NAME',     default='blog_dev'),
        'USER':     config('DB_USER',     default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST':     config('DB_HOST',     default='localhost'),
        'PORT':     config('DB_PORT',     default='5432'),
        'CONN_MAX_AGE': 0,
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
