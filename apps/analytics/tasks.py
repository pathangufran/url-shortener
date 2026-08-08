import logging
from celery import shared_task
from .models import ClickEvent

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},    
)
def record_click_event(
    self,
    *,
    url_id:str,
    ip_address=None,
    country=None,
    user_agent=None,
    referrer=None,
    browser=None,
    device=None,
) -> str:
    """
    Persist a URL click event asynchronously.
    """

    try:
        click_event = ClickEvent.objects.create(
            url_id=url_id,
            ip_address=ip_address,
            country=country,
            user_agent=user_agent,
            referrer=referrer,
            browser=browser,
            device=device,
        )

        logger.info(
            "Click event recorded successfully.",
            extra={
                "click_event_id": str(
                    click_event.id
                ),
                "url_id": str(url_id),
            },
        )

        return str(click_event.id)

    except Exception:
        logger.exception(
            "Failed to record click event.",
            extra={
                "url_id": str(url_id),
            },
        )
        raise