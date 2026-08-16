from .base import *

DEBUG = False

if not SECRET_KEY or SECRET_KEY.startswith("django-insecure-development-only"):
    raise RuntimeError("DJANGO_SECRET_KEY must be set in production.")

if not ALLOWED_HOSTS:
    raise RuntimeError("DJANGO_ALLOWED_HOSTS must be set in production.")

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"