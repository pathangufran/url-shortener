import logging
import string
import secrets
from typing import Optional
from datetime import datetime
from .models import URL
from django.conf import settings
from django.db import IntegrityError,transaction

logger = logging.getLogger(__name__)

BASE62_ALPHABET = (string.ascii_letters + string.digits)

User = settings.AUTH_USER_MODEL

SHORT_CODE_LENGTH = settings.SHORT_CODE_LENGTH

class URLService:
    """
    Handles business logic related to URL shortening.
    """

    def generate_short_code(self) -> str:
        """
        Generate a random Base62 short code.
        """

        return "".join(
            secrets.choice(BASE62_ALPHABET)
            for _ in range(SHORT_CODE_LENGTH)
        )

    def get_unique_short_code(self) -> str:
        """
        Generate a unique short code.
        """

        while True:

            code = self.generate_short_code()
            if not URL.objects.filter(short_code=code).exists():
                return code

    def create_short_url(
        self,
        *,
        user:User,
        long_url:str,
        expires_at: Optional[datetime] = None,
        ) -> str:
        """
        Create a shortened URL.
        """

        max_attempts = 5

        for attempt in range(max_attempts):
            try:
                with transaction.atomic():
                    url = URL.objects.create(
                        user=user,
                        long_url=long_url,
                        short_code=self.get_unique_short_code(),
                        expires_at=expires_at,
                    )
                    logger.info(
                        "Short URL created successfully",
                        extra={
                            "user_id": str(user.id),
                            "url_id": str(url.id),
                            "short_code": url.short_code,
                        },
                    )
                    return url

            except IntegrityError:

                logger.warning(
                    "Short code collision detected. Retrying...",
                    extra={
                        "attempt": attempt + 1,
                    },
                )

        raise RuntimeError("Unable to generate a unique short code.")

