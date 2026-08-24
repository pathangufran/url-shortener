import json
import redis
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class RedisCache:
    """
    Handles Redis operations for URL caching.
    """

    URL_CACHE_PREFIX = "url:"

    def __init__(self):
        self.client = redis.Redis.from_url(
            settings.REDIS_CACHE_URL,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )

    def get_url(self, short_code: str) -> dict:
        """
        Retrieve a cached URL.
        """

        key = self._get_key(short_code)
        try:
            cached_data = self.client.get(key)
            if not cached_data:
                return None

            return json.loads(cached_data)

        except (
            redis.RedisError,
            json.JSONDecodeError,
        ):
            logger.exception(
                "Failed to retrieve URL from Redis.",
                extra={
                    "short_code": short_code,
                    "cache_key": key,
                },
            )
            return None

    def set_url(
        self,
        *,
        short_code: str,
        data: dict,
        ttl: int,
    ) -> bool:
        """
        Store URL data in Redis with TTL.
        """

        key = self._get_key(short_code)
        try:
            self.client.setex(
                key,
                ttl,
                json.dumps(data),
            )
            logger.info(
                "URL cached successfully.",
                extra={
                    "short_code": short_code,
                    "ttl": ttl,
                },
            )
            return True

        except (
            redis.RedisError,
            TypeError,
        ):
            logger.exception(
                "Failed to cache URL.",
                extra={
                    "short_code": short_code,
                },
            )
            return False

    def delete_url(self, short_code: str) -> bool:
        """
        Remove URL from Redis cache.
        """

        key = self._get_key(short_code)
        try:
            deleted = self.client.delete(key)
            logger.info(
                "URL cache invalidated.",
                extra={
                    "short_code": short_code,
                    "deleted": bool(deleted),
                },
            )
            return bool(deleted)

        except redis.RedisError:
            logger.exception(
                "Failed to invalidate URL cache.",
                extra={
                    "short_code": short_code,
                },
            )
            return False

    @classmethod
    def _get_key(cls, short_code: str) -> str:
        """
        Generate Redis cache key.
        """

        return f"{cls.URL_CACHE_PREFIX}{short_code}"
