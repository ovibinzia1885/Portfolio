"""Django settings for the portfolio project."""

import os
import re
from pathlib import Path

import dj_database_url
from decouple import Csv, config
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Security / environment ---------------------------------------------
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())
# e.g. https://example.com,https://www.example.com (needed behind HTTPS proxies)
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())

# Render sets this to the site's own address (e.g. nazmulhoqueovy.onrender.com): always allow it
RENDER_EXTERNAL_HOSTNAME = config("RENDER_EXTERNAL_HOSTNAME", default="")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS = [*ALLOWED_HOSTS, RENDER_EXTERNAL_HOSTNAME]
    CSRF_TRUSTED_ORIGINS = [*CSRF_TRUSTED_ORIGINS, f"https://{RENDER_EXTERNAL_HOSTNAME}"]

# Admin lives at a configurable, non-obvious path in production (e.g. ADMIN_URL=manage-7f3k/)
ADMIN_URL = config("ADMIN_URL", default="admin/").strip().strip("'\"<>")
if "://" in ADMIN_URL:  # a full address was pasted, e.g. https://example.com/my-panel/ -> my-panel/
    ADMIN_URL = ADMIN_URL.split("://", 1)[1].partition("/")[2]
ADMIN_URL = ADMIN_URL.strip("/") + "/" if ADMIN_URL.strip("/") else "admin/"

if not DEBUG:
    if len(SECRET_KEY) < 50 or SECRET_KEY.startswith(("change-me", "django-insecure")):
        raise ImproperlyConfigured("Set a long, random SECRET_KEY in the environment for production.")
    # HTTPS (set SECURE_SSL_REDIRECT=False only if the host already forces HTTPS)
    SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=60 * 60 * 24 * 30, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = config("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True, cast=bool)
    SECURE_HSTS_PRELOAD = config("SECURE_HSTS_PRELOAD", default=False, cast=bool)

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 60 * 60 * 8  # admin session: 8 hours

# Uploads: per-file limit used by apps.core.validators
MAX_UPLOAD_MB = config("MAX_UPLOAD_MB", default=10, cast=int)
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # non-file form data
FILE_UPLOAD_PERMISSIONS = 0o644

# --- Applications --------------------------------------------------------
DJANGO_APPS = [
    "config.admin.PortfolioAdminConfig",  # django.contrib.admin with "Ovy Portfolio" branding
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
]

LOCAL_APPS = [
    "apps.core",
    "apps.education",
    "apps.experience",
    "apps.skills",
    "apps.projects",
    "apps.achievements",
    "apps.certifications",
    "apps.training",
    "apps.blogs",
    "apps.research",
    "apps.contact",
    "apps.analytics",
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serves CSS/JS/images in production (no extra web server)
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.analytics.middleware.VisitorCounterMiddleware",  # anonymous visitor counting
]

# Visitor counting: set True only behind a trusted reverse proxy that sets X-Forwarded-For
TRUST_X_FORWARDED_FOR = config("TRUST_X_FORWARDED_FOR", default=False, cast=bool)

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "apps.core.context_processors.site",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Database ------------------------------------------------------------
# Development: SQLite (default) or local PostgreSQL.
# Production (Neon): DATABASE_URL=postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
DATABASES = {
    "default": dj_database_url.parse(
        config("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=600,
        conn_health_checks=True,  # Neon closes idle connections; reconnect instead of failing
    )
}

# Windows: psycopg's bundled binary DLL can be blocked by Application Control /
# Smart App Control. psycopg then falls back to the system libpq.dll, which it
# looks for on PATH, so put the local PostgreSQL "bin" folder on PATH.
# Set PG_BIN_DIR in .env to override the auto-detected folder.
if os.name == "nt" and DATABASES["default"]["ENGINE"].endswith("postgresql"):
    _pg_bin = config("PG_BIN_DIR", default="")
    if not _pg_bin:
        _found = sorted(
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")).glob(
                "PostgreSQL/*/bin/libpq.dll"
            ),
            key=lambda p: int(p.parent.parent.name) if p.parent.parent.name.isdigit() else 0,
        )
        _pg_bin = str(_found[-1].parent) if _found else ""
    if _pg_bin and _pg_bin not in os.environ.get("PATH", ""):
        os.environ["PATH"] = _pg_bin + os.pathsep + os.environ.get("PATH", "")

# --- Password validation -------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalization ------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = config("TIME_ZONE", default="Asia/Dhaka")
USE_I18N = True
USE_TZ = True

# --- Static & media files ------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Uploaded files: on Cloudinary when CLOUDINARY_URL is set (production: the server disk is temporary),
# otherwise in the local media/ folder. In production without a usable CLOUDINARY_URL, the value saved in
# Admin > Site settings is used instead (see apps.core.storage.ConfiguredMediaStorage).
from apps.core.cloudinary_url import is_valid, masked_shape, normalize_cloudinary_url  # noqa: E402

CLOUDINARY_URL = normalize_cloudinary_url(config("CLOUDINARY_URL", default=""))
CLOUDINARY_URL_PROBLEM = ""
if CLOUDINARY_URL and not is_valid(CLOUDINARY_URL):
    # Never take the whole site down for this: pages keep working (uploaded images are missing) and the
    # problem is logged with the value's shape only (no secret), and shown on the admin dashboard.
    CLOUDINARY_URL_PROBLEM = (
        "CLOUDINARY_URL is malformed, so uploaded files are not served. Expected "
        f"cloudinary://API_KEY:API_SECRET@CLOUD_NAME, got this shape: {masked_shape(CLOUDINARY_URL)}"
    )
    import sys

    print(f"WARNING: {CLOUDINARY_URL_PROBLEM}", file=sys.stderr)
    CLOUDINARY_URL = ""
# The Cloudinary SDK reads this variable by itself when imported: give it the cleaned value, or none
if CLOUDINARY_URL:
    os.environ["CLOUDINARY_URL"] = CLOUDINARY_URL
else:
    os.environ.pop("CLOUDINARY_URL", None)

# Static files in production: hashed + compressed names served by WhiteNoise (long browser caching).
# `python manage.py collectstatic` runs in build.sh on every deploy.
STORAGES = {
    "default": {
        "BACKEND": (
            "apps.core.storage.CloudinaryStorage" if CLOUDINARY_URL
            else "django.core.files.storage.FileSystemStorage" if DEBUG
            else "apps.core.storage.ConfiguredMediaStorage"  # production: value from Admin > Site settings
        )
    },
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"django": {"handlers": ["console"], "level": config("LOG_LEVEL", default="WARNING")}},
}

# Pages may only be framed by this same site (clickjacking protection).
X_FRAME_OPTIONS = "SAMEORIGIN"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
