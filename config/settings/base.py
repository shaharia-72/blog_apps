"""
config/settings/base.py
========================
Base settings shared by ALL environments.
Dev and Prod both import this file and override what they need.
"""

from pathlib import Path
from datetime import timedelta
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY")

# ── Apps ──────────────────────────────────────────────────────
DJANGO_APPS = [
    # "apps.users",
    "admin_interface",  # Beautiful admin — MUST be before django.contrib.admin
    "colorfield",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",  # /sitemap.xml for Google
    "django.contrib.sites",  # Required for django-robots and sitemaps
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "imagekit",
    "django_celery_beat",
    "django_celery_results",
    "storages",
    "robots",
    "cloudinary",
    "cloudinary_storage",
]

LOCAL_APPS = [
    "core",
    "apps.users",
    "apps.blog",
    "apps.projects",
    "apps.analytics",
    "apps.newsletter",
    "apps.contact",
    "apps.monetization",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

SITE_ID = 1  # Required by django.contrib.sites

# ── Middleware ────────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # Before CommonMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.RequestTimingMiddleware",  # Log slow requests
    "core.middleware.SecurityHeadersMiddleware",  # Security headers
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
AUTH_USER_MODEL = "users.User"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ── Locale ────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Dhaka"
USE_I18N = True
USE_TZ = True  # All times stored as UTC, displayed in Asia/Dhaka

# ── Static & Media ────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Storage Configuration ─────────────────────────────────────
USE_CLOUDINARY = config("USE_CLOUDINARY", default=False, cast=bool)

if USE_CLOUDINARY:
    # Cloudinary configuration
    CLOUDINARY_STORAGE = {
        "CLOUD_NAME": config("CLOUD_NAME"),
        "API_KEY": config("API_KEY"),
        "API_SECRET": config("API_SECRET"),
    }
    DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
else:
    # Local file storage
    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# ── Django REST Framework ─────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "200/hour",
        "user": "2000/hour",
        "contact": "5/hour",
        "subscribe": "10/day",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%SZ",
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
}

# ── JWT ───────────────────────────────────────────────────────
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": config("JWT_SECRET_KEY", default=config("SECRET_KEY")),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ── Redis Cache ───────────────────────────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://localhost:6379/0"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"max_connections": 100, "timeout": 20},
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
        },
        "KEY_PREFIX": "blog",
        "TIMEOUT": 60 * 15,
    },
    "sessions": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_SESSION_URL", default="redis://localhost:6379/1"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "TIMEOUT": 60 * 60 * 24 * 7,
    },
}
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "sessions"

# ── Celery ────────────────────────────────────────────────────
CELERY_BROKER_URL = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = "django-db"
CELERY_CACHE_BACKEND = "default"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 min soft limit
CELERY_TASK_TIME_LIMIT = 600  # 10 min hard kill
CELERY_TASK_ROUTES = {
    "apps.newsletter.tasks.*": {"queue": "email"},
    "apps.contact.tasks.*": {"queue": "email"},
    "apps.analytics.tasks.*": {"queue": "analytics"},
}

# ── Email ─────────────────────────────────────────────────────
EMAIL_BACKEND = config(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
ANYMAIL = {
    "SENDGRID_API_KEY": config("SENDGRID_API_KEY", default=""),
    "MAILGUN_API_KEY": config("MAILGUN_API_KEY", default=""),
    "MAILGUN_SENDER_DOMAIN": config("MAILGUN_DOMAIN", default=""),
}
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="hello@yourblog.com")
ADMIN_EMAIL = config("ADMIN_EMAIL", default="admin@yourblog.com")
EMAIL_CONFIRM_TOKEN_EXPIRY = 86400  # 24 hours

# ── API Docs ──────────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "Blog API",
    "DESCRIPTION": "Backend API — System Design, DSA, AI/ML, Python, GenAI blog",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": "/api/v1",
}

# ── CORS ──────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS", default="http://localhost:3000", cast=Csv()
)
CORS_ALLOW_CREDENTIALS = True

# ── Security ─────────────────────────────────────────────────
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Frontend URL ──────────────────────────────────────────────
FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:3000")

# ── Blog-specific settings ────────────────────────────────────
BLOG_SETTINGS = {
    "READING_SPEED_WPM": 200,
    "RELATED_POSTS_COUNT": 3,
    "FEATURED_POSTS_COUNT": 6,
    "CACHE_BLOG_LIST_TTL": 60 * 10,  # 10 min
    "CACHE_BLOG_DETAIL_TTL": 60 * 30,  # 30 min
    "CACHE_ANALYTICS_TTL": 60 * 60,  # 1 hour
    "MAX_COVER_IMAGE_MB": 5,
    "THUMBNAIL_SIZE": (800, 450),  # 16:9
    "OG_IMAGE_SIZE": (1200, 630),  # Open Graph standard
}

# ── SEO Settings ─────────────────────────────────────────────
SEO_SETTINGS = {
    "SITE_NAME": config("SITE_NAME", default="YourBlog"),
    "SITE_URL": config("FRONTEND_URL", default="https://yourblog.com"),
    "DEFAULT_TITLE": config("SEO_DEFAULT_TITLE", default="Backend Engineering Blog"),
    "DEFAULT_DESCRIPTION": config(
        "SEO_DEFAULT_DESC",
        default="In-depth tutorials on System Design, DSA, Django, AI/ML, and Python.",
    ),
    "TWITTER_HANDLE": config("TWITTER_HANDLE", default="@yourhandle"),
    "SCHEMA_ORG_TYPE": "BlogPosting",
}

# ── RSS Feed ──────────────────────────────────────────────────
FEED_SETTINGS = {
    "TITLE": config("SITE_NAME", default="YourBlog") + " — Latest Posts",
    "DESCRIPTION": "Latest articles on System Design, DSA, AI/ML, Python, and more.",
    "ITEMS_COUNT": 20,  # Number of posts in RSS feed
}
