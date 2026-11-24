from .base import *

print("🔧 Running in DEVELOPMENT mode")

DEBUG = True

ALLOWED_HOSTS = ["*"]

# CORS & CSRF settings for development and Cloudflare Tunnel
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [
    "https://*.trycloudflare.com",
    "http://localhost:8003",
    "http://127.0.0.1:8003",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
]

# Database for development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="realsuccess_db"),
        "USER": env("POSTGRES_USER", default="realsuccess_user"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="realsuccess_password"),
        "HOST": env("POSTGRES_HOST", default="db"),
        "PORT": env("POSTGRES_PORT", default="5432"),
    }
}

EMAIL_HOST = env.str("EMAIL_HOST_DEV", default="smtp4dev")
EMAIL_PORT = env.int("EMAIL_PORT_DEV", default=25)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS_DEV", default=False)
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER_DEV", default="")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD_DEV", default="")
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL_DEV", default="no-reply@realsuccess.com")

BREVO_API_KEY = env.str("BREVO_API_KEY", default="")
BREVO_FROM_EMAIL = env.str("BREVO_FROM_EMAIL", default="no-reply@realsuccess.com")
BREVO_FROM_NAME = env.str("BREVO_FROM_NAME", default="Real Success")

# Development logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
