from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse


class HealthCheckTests(TestCase):
    def test_health_check(self):
        response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            {
                "status": "healthy",
            },
        )

    @patch("config.health.RedisCache")
    def test_readiness_check(
        self,
        mock_redis_cache,
    ):
        mock_redis_cache.return_value.client.ping.return_value = True

        response = self.client.get(reverse("readiness"))

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(
            data["status"],
            "ready",
        )

        self.assertTrue(data["checks"]["database"])

        self.assertTrue(data["checks"]["redis"])
