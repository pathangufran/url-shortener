import logging 
import time
import redis
from django.conf import settings

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Redis-backed fixed-window rate limiter.
    """

    def __init__(self,*,prefix="rate_limit",):
       self.prefix = prefix
       self.client = redis.Redis.from_url(
           settings.REDIS_CACHE_URL,
           decode_responses=True,
       ) 

    def is_allowed(self,*,
        identifier:int,
        limit:int,
        window_seconds:int,
    ) -> tuple:
        """
        Check whether a request is allowed.

        Returns:
            tuple:
                (allowed, remaining, retry_after)
        """

        current_window = int(time.time())
        key = (
            f"{self.prefix}:"
            f"{identifier}:"
            f"{current_window}"
        )
        try:
            current_count = self.client.incr(key)
            if current_count == 1:
                self.client.expire(key,window_seconds,)

            remaining = max(limit - current_count,0,)
            ttl = self.client.ttl(key)
            allowed = (current_count <= limit)

            return (allowed,remaining,max(ttl, 0),)

        except redis.RedisError:
            logger.exception(
                "Rate limiter Redis operation failed.",
                extra={
                    "identifier": identifier,
                },
            )
            return (True,limit,0,)