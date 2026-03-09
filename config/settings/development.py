from .base import *  # noqa: F401, F403

DEBUG = True
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
] + MIDDLEWARE  # noqa: F405

INTERNAL_IPS = ["127.0.0.1"]

# Override to use local cache for sessions in development
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
