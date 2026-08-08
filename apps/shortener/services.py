import logging
import string
import secrets
from typing import Optional
from datetime import datetime
from .models import URL
from django.conf import settings
from django.db import IntegrityError,transaction
from django.utils import timezone
from django.db.models import Q

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
                    extra={"attempt": attempt + 1,},
                )

        raise RuntimeError("Unable to generate a unique short code.")

    def get_by_short_code(self,short_code:str) -> dict:
        """
        Retrieve an active URL by its short code.
        """

        url = (
            URL.objects.select_related("user").
            filter(short_code=short_code,is_active=True).first()
        )
        if url is None:
            return None

        if (url.expires_at and url.expires_at <= timezone.now()):
            return "expired"

        logger.info(
            "URL redirected",
            extra={"short_code": url.short_code,"url_id": str(url.id),},
        )

        return url

    def get_url_list(self,user:User) -> list[dict]:
        """
        Base queryset for authenticated user's URLs.

        Filtering, searching, ordering and pagination
        are applied inside the view.
        """
        queryset = (
            URL.objects.select_related("user").
            filter(user=user)
        )
        logger.info(
            "Fetching user URLs.",
            extra={"user_id": str(user.id),},
        )
        return queryset
        
        

        

        
        
