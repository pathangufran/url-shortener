from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from ..models import URL

User = get_user_model()

class URLShortenerAPITestCase(APITestCase):
    """
    Integration/API tests for the URL shortener.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="gufran@example.com",
            password="TestPassword123!",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="TestPassword123!",
        )
        self.client.force_authenticate(user=self.user)

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def create_url(
        self,
        *,
        long_url="https://example.com",
        short_code="abc123",
        expires_at=None,
    ):
        return User.objects.create(
            user=self.user,
            long_url=long_url,
            short_code=short_code,
            expires_at=expires_at
        )

    # ---------------------------------------------------------
    # Create URL
    # ---------------------------------------------------------

    @patch(
        "apps.shortener.views.URLService.create_short_url"
    )
    def test_create_url_success(self,mock_create):
        """
        Authenticated user should be able to create
        a shortened URL.
        """

        url = self.create_url()
        mock_create.return_value = url
        response = self.client.post(
            reverse("create-url"),
            {
                "long_url": "https://google.com",
            },
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        mock_create.assert_called_once()

    def test_create_url_requires_authentication(self):
        """
        Anonymous users should not be able to create URLs.
        """

        self.client.force_authenticate(user=None)
        response = self.client.post(
            reverse("create-url"),
            {
                "long_url": "https://google.com",
            },
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    # ---------------------------------------------------------
    # Custom Alias
    # ---------------------------------------------------------

    def test_create_url_with_custom_alias(self):
        """
        Custom aliases should be accepted.
        """

        response = self.client.post(
            reverse("create-url"),
            {
                "long_url": "https://example.com",
                "custom_alias": "summer-sale",
            },
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        self.assertEqual(
            response.data["short_code"],
            "summer-sale",
        )
        self.assertTrue(
            URL.objects.filter(
                short_code="summer-sale"
            ).exists()
        )

    def test_duplicate_custom_alias_is_rejected(self):
        """
        Duplicate aliases should not be allowed.
        """

        self.create_url(short_code="summer-sale")

        response = self.client.post(
            reverse("create-url"),
            {
                "long_url": "https://example.com",
                "custom_alias": "summer-sale",
            },
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "custom_alias",
            response.data,
        )

    def test_reserved_alias_is_rejected(self):
        """
        Reserved aliases should not be available.
        """

        response = self.client.post(
            reverse("create-url"),
            {
                "long_url": "https://example.com",
                "custom_alias": "admin",
            },
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "custom_alias",
            response.data,
        )

    def test_invalid_custom_alias_is_rejected(self):
        """
        Aliases containing invalid characters should fail.
        """

        response = self.client.post(
            reverse("create-url"),
            {
                "long_url": "https://example.com",
                "custom_alias": "summer sale!",
            },
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "custom_alias",
            response.data,
        )

    # ---------------------------------------------------------
    # Expiration
    # ---------------------------------------------------------

    def test_expiration_must_be_in_future(self):
        """
        Expiration time in the past should be rejected.
        """

        expired_at = timezone.now - timedelta(minutes=5)
        response = self.client.post(
            reverse("create-url"),
            {
                "long_url": "https://example.com",
                "expires_at": expired_at.isoformat(),
            },
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn(
            "expires_at",
            response.data,
        )

    def test_future_expiration_is_accepted(self):
        """
        Future expiration time should be accepted.
        """

        expires_at = timezone.now() + timedelta(hours=1)
        response = self.client.post(
            reverse("create-url"),
            {
                "long_url": "https://example.com",
                "expires_at": expires_at.isoformat(),
            },
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

    # ---------------------------------------------------------
    # Redirect
    # ---------------------------------------------------------

    @patch(
        "apps.shortener.views.AnalyticsService.record_click"
    )
    @patch(
        "apps.shortener.views.URLService.get_by_short_code"
    )
    def test_redirect_success(
        self,
        mock_get_url,
        mock_record_click,
    ):
        """
        Valid short code should redirect to
        the original URL.
        """

        mock_get_url.return_value = {
            "id": "123",
            "long_url": "https://google.com",
            "short_code": "abc123",
            "expires_at": None,
        }

        response = self.client.get(
            reverse(
                "redirect",
                kwargs={
                    "short_code": "abc123"
                },
            )
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_302_FOUND,
        )
        self.assertEqual(
            response.url,
            "https://google.com",
        )

        mock_record_click.assert_called_once()

    @patch(
        "apps.shortener.views.URLService.get_by_short_code"
    )
    def test_redirect_returns_404_for_missing_url(
        self,
        mock_get_url,
    ):
        """
        Missing short code should return 404.
        """

        mock_get_url.return_value = None

        response = self.client.get(
            reverse(
                "redirect",
                kwargs={
                    "short_code": "doesnotexist"
                },
            )
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    @patch(
        "apps.shortener.views.URLService.get_by_short_code"
    )
    def test_redirect_returns_410_for_expired_url(
        self,
        mock_get_url,
    ):
        """
        Expired short URL should return 410 Gone.
        """

        mock_get_url.return_value = "expired"

        response = self.client.get(
            reverse(
                "redirect",
                kwargs={
                    "short_code": "expired-url"
                },
            )
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_410_GONE,
        )

    # ---------------------------------------------------------
    # Authorization
    # ---------------------------------------------------------

    def test_user_cannot_update_another_users_url(self):
        """
        A user should not be able to access another
        user's URL.
        """

        url = URL.objects.create(
            user=self.other_user,
            long_url="https://example.com",
            short_code="other123",
        )

        response = self.client.get(
            reverse(
                "url-detail",
                kwargs={
                    "url_id": url.id,
                },
            )
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    # ---------------------------------------------------------
    # QR Code
    # ---------------------------------------------------------

    @patch(
        "apps.shortener.views.generate_qr_code"
    )
    def test_qr_code_generation(
        self,
        mock_generate_qr,
    ):
        """
        Authenticated owner should be able to
        request a QR code.
        """

        from io import BytesIO

        url = self.create_url(short_code="qr-test")
        qr_buffer = BytesIO(b"fake-png-data")
        mock_generate_qr.return_value = (qr_buffer)

        response = self.client.get(
            reverse(
                "url-qr-code",
                kwargs={
                    "url_id": url.id,
                },
            )
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response["Content-Type"],
            "image/png",
        )

        mock_generate_qr.assert_called_once()

    # ---------------------------------------------------------
    # Pagination / List
    # ---------------------------------------------------------

    def test_list_urls_returns_only_users_urls(self):
        """
        Users should only see URLs belonging to them.
        """

        self.create_url(short_code="mine123")

        URL.objects.create(
            user=self.other_user,
            long_url="https://other.com",
            short_code="other123",
        )

        response = self.client.get(reverse("url-list"))
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        response_data = response.data

        if "results" in response_data:
            results = response_data["results"]
        else:
            results = response_data

        short_codes = [
            item["short_code"]
            for item in results
        ]
        self.assertIn(
            "mine123",
            short_codes,
        )
        self.assertNotIn(
            "other123",
            short_codes,
        )