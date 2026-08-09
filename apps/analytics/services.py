import logging
from .tasks import record_click_event

logger = logging.getLogger(__name__)

class AnalyticsService:
    """
    Handles analytics-related business operations.
    """

    @staticmethod
    def record_click(
        *,
        url_id:str,
        ip_address=None,
        country=None,
        user_agent=None,
        referrer=None,
        browser=None,
        device=None,
    ) -> int:
        """
        Queue a click event for asynchronous processing.

        Analytics is treated as a secondary operation.
        Failure to enqueue the event must not interrupt
        the URL redirect.
        """
        try:
            
            task = record_click_event.delay(
                url_id=str(url_id),
                ip_address=ip_address,
                country=country,
                user_agent=user_agent,
                referrer=referrer,
                browser=browser,
                device=device,
            )
            logger.info(
                "Click analytics task queued.",
                extra={
                    "url_id": str(url_id),
                    "task_id": task.id,
                },
            )

            return task.id

        except Exception:
            logger.exception(
                "Failed to queue click analytics task.",
                extra={
                    "url_id": str(url_id),
                },
            )

            return None