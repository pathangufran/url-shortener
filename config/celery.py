import os
from celery import Celery

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

app = Celery("url_shortener")

app.config_from_object(
    "django.conf:settings",
    namespace="CELERY",
)

app.autodiscover_tasks()

app.conf.beat_schedule.update(
    {
        "deactivate-expired-urls": {
            "task": "apps.shortener.tasks.deactivate_expired_urls",
            "schedule": 60.0,
        },
    }
)