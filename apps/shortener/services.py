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
from .redis_client import RedisCache

logger = logging.getLogger(__name__)

BASE62_ALPHABET = (string.ascii_letters + string.digits)

User = settings.AUTH_USER_MODEL

SHORT_CODE_LENGTH = settings.SHORT_CODE_LENGTH

class URLService:
    """
    Handles business logic related to URL shortening.
    """

    def __init__(self):
        self.cache = RedisCache()

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

        logger.error(
            "Unable to generate a unique short code.",
            extra={
                "user_id": str(user.id),
                "max_attempts": max_attempts,
            },
        )

        raise RuntimeError("Unable to generate a unique short code.")

    def get_by_short_code(self,short_code:str) -> dict:
        """
        Retrieve an active URL.

        Redis is checked first.
        PostgreSQL is the source of truth.
        """

        cached_url = self.cache.get_url(short_code)
        if cached_url:
            logger.info(
                "URL cache hit.",
                extra={"short_code": short_code,},
            )
            return cached_url
        
        logger.info(
            "URL cache miss.",
            extra={"short_code": short_code,},
        )

        url = (
            URL.objects.select_related("user").
            filter(
                short_code=short_code,
                is_active=True
            )
            .first()
        )
        if url is None:
            return None

        if (
            url.expires_at 
            and url.expires_at <= timezone.now()
        ):
            return "expired"

        cache_data = {
            "id": str(url.id),
            "long_url": url.long_url,
            "short_code": url.short_code,
            "expires_at": (
                url.expires_at.isoformat()
                if url.expires_at
                else None
            ),
        }

        ttl = self._calculate_cache_ttl(url.expires_at)
        if ttl > 0:
            self.cache.set_url(
                short_code=short_code,
                data=cache_data,
                ttl=ttl,
            )
        return cache_data

    def _calculate_cache_ttl(self,expires_at=None,) -> int:

        ttl = settings.URL_CACHE_TTL
        if expires_at:
            remaining_seconds = int(
                (expires_at- timezone.now()).total_seconds()
            )

            if remaining_seconds <= 0:
                return 0

            ttl = min(ttl,remaining_seconds,)

        return ttl

    def get_url_list(self,user:User) -> list[dict]:
        """
        Base queryset for authenticated user's URLs.

        Filtering, searching, ordering and pagination
        are applied inside the view.
        """
        queryset = (
            URL.objects.select_related("user").
            filter(user=user,)
        )
        logger.info(
            "Fetching user URLs.",
            extra={"user_id": str(user.id),},
        )
        return queryset

    def get_users_url(self,*,user:User,url_id:str) -> dict:
        """
        Retrieve a URL belonging to the authenticated user.

        Ownership is enforced at the database-query level.
        """

        try:
            url = (
                URL.objects.select_related("user").
                get(id=url_id,user=user,)
            )

        except URL.DoesNotExist:
            logger.warning(
                "URL not found or user does not have access.",
                extra={
                    "user_id": str(user.id),
                    "url_id": str(url_id),
                },
            )
            return None

        logger.info(
            "URL retrieved successfully.",
            extra={
                "user_id": str(user.id),
                "url_id": str(url.id),
                "short_code": url.short_code,
            },
        )

        return url

    @transaction.atomic
    def update_url(self,*,user:User,url_id:str,validated_data:dict) -> dict:
        """
        Update a URL belonging to the authenticated user.
        """
        try:
            url = (
                URL.objects.select_for_update().
                get(user=user,id=url_id,)
            )

        except URL.DoesNotExist:
            logger.warning(
                "URL update failed: URL not found or unauthorized.",
                extra={
                    "user_id": str(user.id),
                    "url_id": str(url_id),
                },
            )
            return None
        
        for field,value in validated_data.items():
            setattr(url, field, value)

        url.save(update_fields=[*validated_data.keys(),"updated_at",])

        self.cache.delete_url(url.short_code)

        logger.info(
            "URL updated successfully.",
            extra={
                "user_id": str(user.id),
                "url_id": str(url.id),
                "short_code": url.short_code,
                "updated_fields": list(
                    validated_data.keys()
                ),
            },
        )

        return url
        
    @transaction.atomic
    def delete_url(self,*,user:User,url_id:str) -> dict:
        """
        Soft delete a URL belonging to the authenticated user.
        """

        try:
            url = (
                URL.objects.select_for_update().
                get(id=url_id,user=user)
            )

        except URL.DoesNotExist:
            logger.warning(
                "URL deletion failed: URL not found or unauthorized.",
                extra={
                    "user_id": str(user.id),
                    "url_id": str(url_id),
                },
            )
            return None

        if not url.is_active:
            logger.info(
                "URL deletion requested for an already inactive URL.",
                extra={
                    "user_id": str(user.id),
                    "url_id": str(url.id),
                    "short_code": url.short_code,
                },
            )
            return url

        url.is_active = False
        url.save(update_fields=["is_active","updated_at",])

        self.cache.delete_url(url.short_code)

        logger.info(
            "URL soft deleted successfully.",
            extra={
                "user_id": str(user.id),
                "url_id": str(url.id),
                "short_code": url.short_code,
            },
        )
        return url


        
        
