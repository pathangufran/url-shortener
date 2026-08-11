from rest_framework.throttling import BaseThrottle
from .rate_limiter import RateLimiter
from rest_framework.views import View
from rest_framework.request import Request

class RedisRateThrottle(BaseThrottle):
    """
    Redis-backed DRF throttle.
    """

    rate_limiter = RateLimiter()
    limit = 100
    window_seconds = 60

    def allow_request(self,request:Request,view:View) -> bool:

        identifier = self.get_identifier(request)
        allowed, remaining, retry_after = (
            self.rate_limiter.is_allowed(
                identifier=identifier,
                limit=self.limit,
                window_seconds=self.window_seconds,
            )
        )

        self.remaining = remaining
        self.retry_after = retry_after

        return allowed

    def wait(self) -> None:
        if self.retry_after:
            return self.retry_after

        return None

    @staticmethod
    def get_identifier(request:Request) -> str:
        """
        Identify the client.

        Authenticated users are identified by user ID.
        Anonymous users are identified by IP.
        """

        if request.user.is_authenticated:
            return (f"user:{request.user.id}")

        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

        if forwarded_for:
            ip_address = (forwarded_for.split(",")[0].strip())
        else:
            ip_address = request.META.get("REMOTE_ADDR","unknown",)

        return f"ip:{ip_address}"

class AuthenticationRateThrottle(RedisRateThrottle):
    """
    Strict throttle for authentication endpoints.
    """

    limit = 10
    window_seconds = 60

class URLCreationRateThrottle(RedisRateThrottle):
    """
    Throttle for URL creation.
    """

    limit = 30
    window_seconds = 60


class AnalyticsRateThrottle(RedisRateThrottle):
    """
    Throttle for analytics APIs.
    """

    limit = 60
    window_seconds = 60


class RedirectRateThrottle(RedisRateThrottle):
    """
    High-volume throttle for redirects.
    """

    limit = 300
    window_seconds = 60