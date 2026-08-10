import logging
from .tasks import record_click_event
from .models import ClickEvent
from django.conf import settings
from django.db.models import Count
from apps.shortener.models import URL
from datetime import datetime,time,timedelta
from django.utils import timezone

User = settings.AUTH_USER_MODEL

logger = logging.getLogger(__name__)

class AnalyticsService:
    """
    Handles analytics-related business operations.
    """

    BREAKDOWN_LIMIT = 10

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

    @staticmethod
    def get_url_analytics(*,user:User,url_id:str,
        start_date=None,end_date=None) -> list[dict]:
        """
        Generate analytics for a URL owned by the
        authenticated user.
        """

        try:

            url = URL.objects.get(id=url_id,user=user)

        except URL.DoesNotExist:
            logger.warning(
                "Analytics requested for missing or unauthorized URL.",
                extra={
                    "user_id": str(user.id),
                    "url_id": str(url_id),
                },
            )
            return None

        click_events = ClickEvent.objects.filter(url=url)
        if start_date:
            start_datetime = timezone.make_aware(
                datetime.combine(
                    start_date,
                    time.min,
                )
            )

            click_events = click_events.filter(
                clicked_at__gte=start_datetime
            )

        if end_date:
            end_datetime = timezone.make_aware(
                datetime.combine(
                    end_date + timedelta(days=1),
                    time.min,
                )
            )

            click_events = click_events.filter(
                clicked_at__lt=end_datetime
            )
        total_clicks = click_events.count()

        unique_visitors = (
            click_events
            .exclude(ip_address__isnull=True)
            .exclude(ip_address="")
            .values("ip_address")
            .distinct()
            .count()
        )

        top_countries = (
            click_events
            .exclude(country__isnull=True)
            .exclude(country="")
            .values("country")
            .annotate(clicks=Count("id"))
            .order_by("-clicks", "country")[
                :AnalyticsService.BREAKDOWN_LIMIT
            ]
        )

        top_browsers = (
            click_events
            .exclude(browser__isnull=True)
            .exclude(browser="")
            .values("browser")
            .order_by("-clicks", "browser")[
                :AnalyticsService.BREAKDOWN_LIMIT
            ]
        )

        top_devices = (
            click_events
            .exclude(device__isnull=True)
            .exclude(device="")
            .values("device")
            .annotate(clicks=Count("id"))
            .order_by("-clicks", "device")[
                :AnalyticsService.BREAKDOWN_LIMIT
            ]
        )

        top_referrers = (
            click_events
            .exclude(referrer__isnull=True)
            .exclude(referrer="")
            .values("referrer")
            .annotate(clicks=Count("id"))
            .order_by("-clicks", "referrer")[
                :AnalyticsService.BREAKDOWN_LIMIT
            ]
        )

        analytics = {
            "total_clicks": total_clicks,
            "unique_visitors": unique_visitors,
            "top_countries": [
                {
                    "country": item["country"],
                    "clicks": item["clicks"],
                }
                for item in top_countries
            ],
            "top_browsers": [
                {
                    "browser": item["browser"],
                    "clicks": item["clicks"],
                }
                for item in top_browsers
            ],
            "top_devices": [
                {
                    "device": item["device"],
                    "clicks": item["clicks"],
                }
                for item in top_devices
            ],
            "top_referrers": [
                {
                    "referrer": item["referrer"],
                    "clicks": item["clicks"],
                }
                for item in top_referrers
            ],
        }

        logger.info(
            "URL analytics generated successfully.",
            extra={
                "user_id": str(user.id),
                "url_id": str(url.id),
                "start_date": (
                    str(start_date)
                    if start_date
                    else None
                ),
                "end_date": (
                    str(end_date)
                    if end_date
                    else None
                ),
                "total_clicks": total_clicks,
                "unique_visitors": unique_visitors,
            },
        )

        return analytics

    @staticmethod
    def get_click_events(
        *,
        user:User,
        url_id:str,
        start_date=None,
        end_date=None,
        browser=None,
        device=None,
        country=None,
        ordering="-clicked_at",
    ) -> list[dict]:
        """
        Return click events for a URL owned by the
        authenticated user.

        Filtering and ordering are performed by PostgreSQL.
        """

        try:
            url = (
                URL.objects.get(id=url_id,user=user)
            )

        except URL.DoesNotExist:
            logger.warning(
                "Click events requested for missing "
                "or unauthorized URL.",
                extra={
                    "user_id": str(user.id),
                    "url_id": str(url_id),
                },
            )
            return None

        queryset = (
            ClickEvent.objects
            .filter(url=url)
            .only(
                "id",
                "ip_address",
                "country",
                "browser",
                "device",
                "referrer",
                "clicked_at",
            )
        )
        if start_date:
            start_datetime = timezone.make_aware(
                datetime.combine(
                    start_date,
                    time.min,
                )
            )

            queryset = queryset.filter(
                clicked_at__gte=start_datetime
            )
        if end_date:
            end_datetime = timezone.make_aware(
                datetime.combine(
                    end_date + timedelta(days=1),
                    time.min,
                )
            )

            queryset = queryset.filter(
                clicked_at__lt=end_datetime
            )

        if browser:
            queryset = queryset.filter(
                browser__iexact=browser
            )

        if device:
            queryset = queryset.filter(
                device__iexact=device
            )

        if country:
            queryset = queryset.filter(
                country__iexact=country
            )

        allowed_ordering = {
            "clicked_at",
            "-clicked_at",
            "browser",
            "-browser",
            "device",
            "-device",
        }

        if ordering not in allowed_ordering:
            ordering = "-clicked_at"

        queryset = queryset.order_by(ordering)

        logger.info(
            "Click events fetched successfully.",
            extra={
                "user_id": str(user.id),
                "url_id": str(url.id),
                "start_date": (
                    str(start_date)
                    if start_date
                    else None
                ),
                "end_date": (
                    str(end_date)
                    if end_date
                    else None
                ),
                "browser": browser,
                "device": device,
                "country": country,
                "ordering": ordering,
            },
        )

        return queryset
