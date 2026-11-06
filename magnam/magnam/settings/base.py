import os
from pathlib import Path
from dotenv import load_dotenv
import sentry_sdk

BASE_DIR = Path(__file__).resolve().parent.parent.parent

ENV_FILE = os.getenv("DJANGO_ENV_FILE", ".env.development")
ENV_FILE_PATH = Path(ENV_FILE)

if not ENV_FILE_PATH.is_absolute():
    ENV_FILE_PATH = BASE_DIR / ENV_FILE_PATH

load_dotenv(ENV_FILE_PATH)

# ---------------------------------------------------------------------
# SECURITY
# ---------------------------------------------------------------------

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is missing.")

# since venv contains strings and not booleans we default to 'False' not to False
DEBUG = os.getenv("DEBUG", "False").lower() == "true"


# ---------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django_crontab",
    "django.contrib.postgres",
    "daphne",  # needs to come before staticfiles
    "django.contrib.staticfiles",
    "channels",
    "rest_framework",
    "corsheaders",
    "webpack_loader",
    "NewsPageApp",
    "MangaPageApp",
    "PortfolioPageApp",
    "CompetitionPageApp",
    "ProfilePageApp",
    "KanbanTaskPageApp",
    "frontend",
]


# ---------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "magnam.urls"

WSGI_APPLICATION = "magnam.wsgi.application"
ASGI_APPLICATION = "magnam.asgi.application"

CORS_ALLOW_CREDENTIALS = True

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"

SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"

# ---------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------

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
            ]
        },
    }
]


# ---------------------------------------------------------------------
# REST Framework
# ---------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
}

SESSION_ENGINE = "django.contrib.sessions.backends.db"


# ---------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

FRONTEND_URL = os.getenv("FRONTEND_URL")


# ---------------------------------------------------------------------
# Media
# ---------------------------------------------------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT"))

# this one is used to overwrite the settings.MEDIA_ROOT when test are run
TEST_MEDIA_ROOT = Path(
    os.getenv("TEST_MEDIA_ROOT", BASE_DIR.parent / "magnam_database_test")
)

COMPETITIONS_MEDIA_FOLDERNAME = "magnam_competitions"
NEWS_MEDIA_FOLDERNAME = "magnam_news"
MANGAS_MEDIA_FOLDERNAME = "magnam_mangas"
PORTFOLIOS_MEDIA_FOLDERNAME = "magnam_portfolios"
PROFILES_MEDIA_FOLDERNAME = "magnam_profiles"
# ---------------------------------------------------------------------
# Static
# ---------------------------------------------------------------------

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# ---------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------
STORAGE_PROVIDER = os.getenv("STORAGE_PROVIDER", "local")


if STORAGE_PROVIDER == "r2":

    STORAGES = {
        "default": {"BACKEND": "magnam.storage.backends.r2.R2Storage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }

else:

    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }


R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL")

# ---------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------

# celery stuff for async pdf parsing
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_WORKER_MAX_MEMORY_PER_CHILD = 1000000  # ~1GB
CELERY_WORKER_MAX_TASKS_PER_CHILD = 50  # restart after executing 50 tasks


# ---------------------------------------------------------------------
# Channels
# ---------------------------------------------------------------------

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                (
                    os.getenv("REDIS_HOST", "127.0.0.1"),
                    int(os.getenv("REDIS_PORT", 6379)),
                )
            ]
        },
    }
}


# ---------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Istanbul"

USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DISABLE_EXTERNAL_CALLS_FOR_TESTING = False

CRONJOBS = [
    (
        "0 3 * * *",  # 3:00 AM every day
        "ProfilePageApp.cron.delete_expired_unverified_profiles",
    )
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOG_DIR = Path(os.getenv("LOG_DIR"))
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"}
    },
    "handlers": {
        "cron_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"{LOG_DIR}/cron_tasks.log",
            "maxBytes": 1024 * 1024 * 10,
            "backupCount": 5,
            "formatter": "verbose",
        },
        "pdf_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"{LOG_DIR}/pdf_processing.log",
            "maxBytes": 1024 * 1024 * 10,
            "backupCount": 5,
            "formatter": "verbose",
        },
        "profile_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"{LOG_DIR}/profile.log",
            "maxBytes": 1024 * 1024 * 10,
            "backupCount": 5,
            "formatter": "verbose",
        },
        "in_app_transactions_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"{LOG_DIR}/in_app_transactions.log",
            "maxBytes": 1024 * 1024 * 10,
            "backupCount": 5,
            "formatter": "verbose",
        },
        "django_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"{LOG_DIR}/django.log",
            "maxBytes": 1024 * 1024 * 10,
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "cron_logger": {"handlers": ["cron_file"], "level": "INFO", "propagate": False},
        "pdf_logger": {"handlers": ["pdf_file"], "level": "INFO", "propagate": False},
        "profile_logger": {
            "handlers": ["profile_file"],
            "level": "INFO",
            "propagate": False,
        },
        "in_app_transactions": {
            "handlers": ["in_app_transactions_file"],
            "level": "INFO",
            "propagate": False,
        },
        "django": {"handlers": ["django_file"], "level": "INFO", "propagate": False},
    },
}

SENTRY_DSN = os.getenv("SENTRY_DSN")

if SENTRY_DSN:
    sentry_sdk.init(dsn=SENTRY_DSN, send_default_pii=False)
