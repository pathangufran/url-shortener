from unittest.mock import patch

from rest_framework.test import APITestCase

from apps.shortener.utils.rate_limiter import RateLimiter


class RateLimiterTestCase(APITestCase):
    """
    Tests for Redis-backed rate limiting.
    """

    @patch("apps.shortener.utils.rate_limiter.redis.Redis.from_url")
    def test_request_allowed_under_limit(
        self,
        mock_redis,
    ):

        mock_client = mock_redis.return_value

        mock_client.incr.return_value = 1
        mock_client.ttl.return_value = 59

        limiter = RateLimiter()

        allowed, remaining, retry_after = limiter.is_allowed(
            identifier="user:123",
            limit=10,
            window_seconds=60,
        )

        self.assertTrue(allowed)
        self.assertEqual(
            remaining,
            9,
        )
        self.assertEqual(
            retry_after,
            59,
        )

    @patch("apps.shortener.utils.rate_limiter.redis.Redis.from_url")
    def test_request_rejected_over_limit(
        self,
        mock_redis,
    ):

        mock_client = mock_redis.return_value

        mock_client.incr.return_value = 11
        mock_client.ttl.return_value = 45

        limiter = RateLimiter()

        allowed, remaining, retry_after = limiter.is_allowed(
            identifier="user:123",
            limit=10,
            window_seconds=60,
        )

        self.assertFalse(allowed)
        self.assertEqual(
            remaining,
            0,
        )
        self.assertEqual(
            retry_after,
            45,
        )
