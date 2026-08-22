from uuid import uuid4

from django.db import models

from apps.shortener.models import URL


class ClickEvent(models.Model):
    """
    Represents a single click on a shortened URL.
    """

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    url = models.ForeignKey(
        URL,
        on_delete=models.CASCADE,
        related_name="click_events",
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )
    country = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
    )
    referrer = models.URLField(
        null=True,
        blank=True,
    )
    browser = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )
    device = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )
    clicked_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        db_table = "click_events"

        indexes = [
            models.Index(
                fields=["url", "-clicked_at"],
            ),
            models.Index(
                fields=["url", "ip_address"],
            ),
            models.Index(
                fields=["country"],
            ),
            models.Index(
                fields=["browser"],
            ),
        ]
        ordering = ["-clicked_at"]

    def __str__(self):
        return f"{self.url.short_code} - {self.clicked_at}"
