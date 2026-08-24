from unittest.mock import patch

import redis
from rest_framework.test import APITestCase

from apps.shortener.utils.redis_client import RedisCache


class RedisCacheTestCase(APITestCase):
    """
    Tests for Redis URL caching.
    """

    @patch("apps.shortener.utils.redis_client.redis.Redis.from_url")
    def test_set_and_get_url(
        self,
        mock_redis,
    ):

        mock_client = mock_redis.return_value

        mock_client.get.return_value = '{"long_url": "https://example.com"}'

        cache = RedisCache()

        result = cache.get_url("abc123")
        self.assertEqual(
            result["long_url"],
            "https://example.com",
        )

        mock_client.get.assert_called_once_with("url:abc123")

    @patch("apps.shortener.utils.redis_client.redis.Redis.from_url")
    def test_delete_url(
        self,
        mock_redis,
    ):

        mock_client = mock_redis.return_value
        mock_client.delete.return_value = 1

        cache = RedisCache()

        result = cache.delete_url("abc123")

        self.assertTrue(result)

        mock_client.delete.assert_called_once_with("url:abc123")

    @patch("apps.shortener.utils.redis_client.redis.Redis.from_url")
    def test_cache_failure_does_not_raise(
        self,
        mock_redis,
    ):

        mock_client = mock_redis.return_value

        mock_client.get.side_effect = redis.RedisError("Redis unavailable")

        cache = RedisCache()

        result = cache.get_url("abc123")

        self.assertIsNone(result)
