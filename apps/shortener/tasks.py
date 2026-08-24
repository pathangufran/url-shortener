import logging
from celery import shared_task
from django.utils import timezone
from .models import URL

logger = logging.getLogger(__name__)

@shared_task
def deactivate_expired_urls() -> int:
    """
    Deactivate URLs whose expiration time has passed.
    """

    now = timezone.now()

    updated_count = URL.objects.filter(
        is_active=True,
        expires_at__isnull=False,
        expires_at__lte=now,
    ).update(
        is_active=False,
    )

    logger.info(
        "Expired URLs deactivated.",
        extra={
            "updated_count": updated_count,
        },
    )

    return updated_count
