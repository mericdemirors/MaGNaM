import os
from .base import *

if STORAGE_PROVIDER == "local":
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".ngrok-free.dev"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "TEST": {"NAME": "test_" + os.getenv("POSTGRES_DB", "magnam_db")},
    }
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]

CSRF_TRUSTED_ORIGINS = ["http://localhost:3000", "https://*.ngrok-free.dev"]

WEBPACK_LOADER = {
    "DEFAULT": {
        "CACHE": False,
        "BUNDLE_DIR_NAME": "frontend/",
        "STATS_FILE": BASE_DIR / "frontend/static/frontend/webpack-stats.json",
    }
}
