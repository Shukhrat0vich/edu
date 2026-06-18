"""
Development settings for EduAnalytics.
"""

import os
from dotenv import load_dotenv
from .base import *  # noqa

# .env faylni yuklash
load_dotenv()

# Debug
DEBUG = True

ALLOWED_HOSTS = ["*"]

# =========================
# DATABASE CONFIG
# =========================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "eduanalytics"),
        "USER": os.getenv("POSTGRES_USER", "eduuser"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "edupass"),
        "HOST": os.getenv("POSTGRES_HOST", "db"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),  # Docker port
    }
}

# =========================
# Django Debug Toolbar (optional)
# =========================

INTERNAL_IPS = ["127.0.0.1"]