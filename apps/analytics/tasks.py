import ipaddress
import logging
from celery import shared_task
from user_agents import parse
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
    url_id: str,
    ip_address=None,
    country=None,
    user_agent=None,
    referrer=None,
    browser=None,
    device=None,
) -> str:
    """
    Persist a URL click event asynchronously.

    User-Agent parsing is intentionally performed inside
    the background worker so it does not increase redirect latency.
    """

    try:
        browser = None
        device = None

        if user_agent:
            parsed_user_agent = parse(user_agent)
            browser = parsed_user_agent.browser.family

            if parsed_user_agent.is_mobile:
                device = "Mobile"
            elif parsed_user_agent.is_tablet:
                device = "Tablet"
            elif parsed_user_agent.is_pc:
                device = "Desktop"
            elif parsed_user_agent.is_bot:
                device = "Bot"
            else:
                device = "Other"

        try:
            ip_address = str(ipaddress.ip_address(ip_address)) if ip_address else None
        except ValueError:
            ip_address = None

        click_event = ClickEvent.objects.create(
            url_id=url_id,
            ip_address=ip_address,
            country=country,
            user_agent=(user_agent or "")[:1000] or None,
            referrer=(referrer or "")[:200] or None,
            browser=browser,
            device=device,
        )

        logger.info(
            "Click event recorded successfully.",
            extra={
                "click_event_id": str(click_event.id),
                "url_id": str(url_id),
                "browser": browser,
                "device": device,
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
