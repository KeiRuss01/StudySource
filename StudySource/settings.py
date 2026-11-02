import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

# Load values from StudySource/.env
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def env_list(name, default=""):
    return [
        value.strip()
        for value in os.getenv(name, default).split(",")
        if value.strip()
    ]


SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-local-development-only",
)

DEBUG = env_bool("DJANGO_DEBUG", default=False)

ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    default="127.0.0.1,localhost",
)
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "study.apps.StudyConfig",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "StudySource.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


WSGI_APPLICATION = "StudySource.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "postgres"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "OPTIONS": {
            "sslmode": os.getenv("DB_SSLMODE", "require"),
        },
        "CONN_MAX_AGE": 60,
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Manila"
USE_I18N = True
USE_TZ = True


STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}

# Render terminates HTTPS at its reverse proxy and forwards the original
# scheme in this header. Secure cookies are enabled whenever DEBUG is off.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = env_bool(
    "DJANGO_SECURE_SSL_REDIRECT",
    default=False,
)


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# This must be configured before creating the first migration.
AUTH_USER_MODEL = "study.User"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "student_dashboard"
LOGOUT_REDIRECT_URL = "home"
