from .base import *

DEBUG = True

INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405

MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE  # noqa: F405

INTERNAL_IPS = ["127.0.0.1"]

# Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Console email backend
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Relax throttling during development
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "burst": "1000/min",
    "sustained": "100000/day",
    "anon": "1000/min",
}

# Show SQL queries
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
}