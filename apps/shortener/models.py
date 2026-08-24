from django.db import models
from django.conf import settings
from apps.common.models import TimeStampedModel

class URL(TimeStampedModel):
    """
    Stores the mapping between a long URL and its shortened code.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="urls",
    )
    long_url = models.URLField()
    short_code = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(
        default=True,
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "urls"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["is_active", "expires_at"]),
        ]

    def __str__(self):
        return self.short_code
