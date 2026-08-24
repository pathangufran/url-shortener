from datetime import timedelta
from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.shortener.models import URL
from apps.shortener.services import URLService
from config.exceptions import URLExpiredException, URLNotFoundException


class URLServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="owner@example.com", password="secure-test-password"
        )
        self.cache = Mock()
        self.service = URLService(cache=self.cache)

    def test_custom_alias_returns_created_url(self):
        url = self.service.create_short_url(
            user=self.user, long_url="https://example.com", custom_alias="campaign"
        )
        self.assertEqual(url.short_code, "campaign")

    def test_missing_code_raises_not_found(self):
        self.cache.get_url.return_value = None
        with self.assertRaises(URLNotFoundException):
            self.service.get_by_short_code("missing")

    def test_expired_cached_url_is_not_redirected(self):
        self.cache.get_url.return_value = {
            "id": "1",
            "long_url": "https://example.com",
            "expires_at": (timezone.now() - timedelta(seconds=1)).isoformat(),
        }
        with self.assertRaises(URLExpiredException):
            self.service.get_by_short_code("expired")
        self.cache.delete_url.assert_called_once_with("expired")

    def test_malformed_cache_entry_falls_back_to_database(self):
        URL.objects.create(
            user=self.user,
            long_url="https://example.com",
            short_code="valid",
        )
        self.cache.get_url.return_value = {"expires_at": "not-a-date"}
        result = self.service.get_by_short_code("valid")
        self.assertEqual(result["long_url"], "https://example.com")
