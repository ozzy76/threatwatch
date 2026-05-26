import os
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY")

DEBUG = False

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

# --- Django apps (no django.contrib.auth ORM models; we use MongoEngine) ---
INSTALLED_APPS = [
    # Django internals
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # Third-party
    "whitenoise.runserver_nostatic",
    "csp",
    # Project apps
    "apps.accounts",
    "apps.customers",
    "apps.threats",
    "apps.detections",
    "apps.reports",
    "apps.fair",
    "apps.gamification",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "apps.accounts.middleware.MongoAuthMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "csp.middleware.CSPMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- No Django ORM DB (MongoEngine handles persistence) ---
DATABASES = {}

# --- MongoDB via MongoEngine ---
import sys
import certifi
import mongoengine

MONGODB_URI = config("MONGODB_URI")

if "test" in sys.argv:
    # Use mongomock for unit tests
    import mongomock
    mongoengine.connect("test_db", host="localhost", mongo_client_class=mongomock.MongoClient, alias="default")
else:
    try:
        # Connect to remote Atlas MongoDB, but with a timeout so it doesn't hang forever offline
        mongoengine.connect(
            host=MONGODB_URI,
            alias="default",
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=2000,
            connectTimeoutMS=2000
        )
    except Exception as e:
        print(f"Warning: Remote MongoDB connection failed ({e}). Falling back to in-memory mongomock.")
        import mongomock
        mongoengine.connect("fallback_db", host="localhost", mongo_client_class=mongomock.MongoClient, alias="default")



# --- Custom auth backend ---
AUTHENTICATION_BACKENDS = ["apps.accounts.backends.MongoEngineBackend"]

# --- Session: Redis-backed ---
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 28800  # 8 hours

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://127.0.0.1:6379/0"),
    }
}

# --- Static files ---
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# --- Media ---
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# --- Security headers ---
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True

# --- CSP (django-csp 4.0 uses CONTENT_SECURITY_POLICY dict) ---
CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ["'self'"],
        "script-src": ["'self'", "'unsafe-inline'"],
        "style-src": ["'self'", "'unsafe-inline'", "https://fonts.bunny.net"],
        "font-src": ["'self'", "https://fonts.bunny.net"],
        "img-src": ["'self'", "data:", "https://*"],
        "object-src": ["'none'"],
        "base-uri": ["'self'"],
        "form-action": ["'self'", "https://accounts.google.com", "https://login.microsoftonline.com", "https://*.okta.com"],
        "frame-ancestors": ["'none'"],
    }
}

# --- OIDC SSO Configuration ---
OIDC_SANDBOX_MODE = config("OIDC_SANDBOX_MODE", default="True", cast=bool)
OIDC_PROVIDERS = {
    "google": {
        "name": "Google",
        "client_id": config("OIDC_GOOGLE_CLIENT_ID", default="mock-google-client-id"),
        "client_secret": config("OIDC_GOOGLE_CLIENT_SECRET", default="mock-google-client-secret"),
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
        "scope": "openid email profile",
    },
    "entra": {
        "name": "Microsoft Entra ID",
        "client_id": config("OIDC_ENTRA_CLIENT_ID", default="mock-entra-client-id"),
        "client_secret": config("OIDC_ENTRA_CLIENT_SECRET", default="mock-entra-client-secret"),
        "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "userinfo_url": "https://graph.microsoft.com/oidc/userinfo",
        "scope": "openid email profile",
    },
    "okta": {
        "name": "Okta",
        "client_id": config("OIDC_OKTA_CLIENT_ID", default="mock-okta-client-id"),
        "client_secret": config("OIDC_OKTA_CLIENT_SECRET", default="mock-okta-client-secret"),
        "auth_url": "https://login.okta.com/oauth2/v1/authorize",
        "token_url": "https://login.okta.com/oauth2/v1/token",
        "userinfo_url": "https://login.okta.com/oauth2/v1/userinfo",
        "scope": "openid email profile",
    }
}

# --- GCS ---
GCS_BUCKET_NAME = config("GCS_BUCKET_NAME", default="threatwatch-reports")

# --- Logging ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "logging.Formatter",
            "format": '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "apps.accounts": {"level": "INFO", "propagate": True},
        "apps.reports": {"level": "INFO", "propagate": True},
    },
}

# --- i18n ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
