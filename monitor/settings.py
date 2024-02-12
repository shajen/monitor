import os
import re
import sys
import tzlocal
import zoneinfo
import json
from django.template import base

base.tag_re = re.compile(base.tag_re.pattern, re.DOTALL)
sys.path.append(os.path.dirname(__file__))

DEBUG = False

ALLOWED_HOSTS = ["*"]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "public", "static")
STATICFILES_DIRS = [os.path.join(os.path.dirname(__file__), "static/")]

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "public", "media")

DATABASES = {
    "default": json.loads(
        os.getenv("DATABASE") or '{"ENGINE": "django.db.backends.sqlite3","NAME": "db/monitor.sqlite3"}'
    )
}

MQTT = {
    "host": os.getenv("MQTT_HOST") or "sdr-broker",
    "port_tcp": int(os.getenv("MQTT_PORT_TCP") or "1883"),
    "port_ws": int(os.getenv("MQTT_PORT_WS") or "9001"),
    "user": os.getenv("MQTT_USER") or "admin",
    "password": os.getenv("MQTT_PASSWORD") or "password",
}

TUYA = {
    "endpoint": os.getenv("TUYA_ENDPOINT") or "https://openapi.tuyaeu.com",
    "access_id": os.getenv("TUYA_ACCESS_ID") or "01234567890123456789",
    "access_key": os.getenv("TUYA_ACCESS_KEY") or "01234567890123456789",
    "user": os.getenv("TUYA_USER") or "test@test",
    "password": os.getenv("TUYA_PASSWORD") or "0123456789",
}

IP_GEOLOCATION_API_KEY = os.getenv("IP_GEOLOCATION_API_KEY") or "01234567890123456789012345678901"

FALLBACK_API_KEY = os.getenv("FALLBACK_API_KEY") or "password"

FULL_MODE_ENABLED = (os.getenv("FULL_MODE_ENABLED") or "false").lower() in ["true", "t", "1"]

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(os.path.dirname(__file__), "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "graphs.context_processors.sensor_groups",
                "graphs.context_processors.sensor_types",
                "graphs.context_processors.full_mode_enabled",
            ],
        },
    },
]

SECRET_KEY = os.getenv("SECRET_KEY") or "01234567890123456789012345678901234567891234567890"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
    "django_cleanup.apps.CleanupConfig",
    "django_bootstrap_icons",
    "debug_toolbar",
    "crispy_forms",
    "crispy_bootstrap5",
    "graphs",
    "logs",
    "sdr",
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[{asctime}.{msecs:0<3.0f}][{module:15s}][{name:13s}][{levelname:7s}] {message:s}",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django.db": {"level": "INFO"},
        "django.db.backends": {
            "level": "INFO",
            "handlers": ["console"],
        },
    },
}

LOGIN_REDIRECT_URL = "index"
LOGOUT_REDIRECT_URL = "index"

ROOT_URLCONF = "monitor.urls"

WSGI_APPLICATION = "monitor.wsgi.application"

LANGUAGE_CODE = "en"


def detect_timezone():
    timezone = tzlocal.get_localzone_name()
    if timezone:
        try:
            zoneinfo.ZoneInfo(timezone)
            return timezone
        except:
            pass
    else:
        return "UTC"


TIME_ZONE = detect_timezone()

USE_I18N = True

USE_L10N = False
DATE_FORMAT = "Y-m-d"
DATETIME_FORMAT = "Y-m-d H:i:s"
SHORT_DATETIME_FORMAT = "Y-m-d H:i:s"

USE_TZ = True

REGISTRATION_OPEN = False

INTERNAL_IPS = ["127.0.0.1"]
