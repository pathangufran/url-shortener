import logging
import secrets
import string
from datetime import datetime
from typing import Protocol

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from config.exceptions import (
    DuplicateAliasException,
    ShortCodeGenerationException,
    URLExpiredException,
    URLNotFoundException,
)

from .models import URL
from .utils.redis_client import RedisCache

logger = logging.getLogger(__name__)

User = settings.AUTH_USER_MODEL

BASE62_ALPHABET = string.ascii_letters + string.digits

SHORT_CODE_LENGTH = settings.SHORT_CODE_LENGTH


class ShortCodeGenerator(Protocol):
    """
    Contract for short-code generators.
    """

    def generate(self) -> str: ...


class Base62ShortCodeGenerator:
    """
    Generates random Base62 short codes.
    """

    def generate(self) -> str:

        return "".join(
            secrets.choice(BASE62_ALPHABET) for _ in range(SHORT_CODE_LENGTH)
        )


class URLService:
    """
    Handles business logic related to URL shortening.
    """

    def __init__(
        self,
        cache=None,
        short_code_generator=None,
    ):
        self.cache = cache or RedisCache()
        self.short_code_generator = short_code_generator or Base62ShortCodeGenerator()

    def generate_short_code(self) -> str:
        """
        Generate a random Base62 short code.
        """

        return self.short_code_generator.generate()

    def get_unique_short_code(self) -> str:
        """
        Generate a unique short code.
        """

        for _ in range(20):
            code = self.generate_short_code()

            if not URL.objects.filter(short_code=code).exists():
                return code
        raise ShortCodeGenerationException()

    def _build_cache_data(
        self,
        url: URL,
    ) -> dict:
        return {
            "id": str(url.id),
            "long_url": url.long_url,
            "short_code": url.short_code,
            "expires_at": (url.expires_at.isoformat() if url.expires_at else None),
        }

    def create_short_url(
        self,
        *,
        user: User,
        long_url: str,
        expires_at: datetime | None = None,
        custom_alias=None,
    ) -> URL:
        """
        Create a shortened URL using either a custom alias
        or a generated short code.
        """

        max_attempts = 5
        if custom_alias:
            try:
                url = URL.objects.create(
                    user=user,
                    long_url=long_url,
                    short_code=custom_alias,
                    expires_at=expires_at,
                )

            except IntegrityError:
                logger.warning(
                    "Custom alias creation failed due to duplicate alias.",
                    extra={
                        "user_id": str(user.id),
                        "custom_alias": custom_alias,
                    },
                )

                raise DuplicateAliasException()

            logger.info(
                "Short URL created with custom alias.",
                extra={
                    "user_id": str(user.id),
                    "url_id": str(url.id),
                    "short_code": url.short_code,
                },
            )

            return url

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

        logger.error(
            "Unable to generate a unique short code.",
            extra={
                "user_id": str(user.id),
                "max_attempts": max_attempts,
            },
        )

        raise ShortCodeGenerationException()

    def get_by_short_code(self, short_code: str) -> dict:
        """
        Retrieve an active URL.

        Redis is checked first.
        PostgreSQL is the source of truth.
        """

        cached_url = self.cache.get_url(short_code)
        if cached_url:
            expires_at = cached_url.get("expires_at")
            if expires_at:
                try:
                    is_expired = datetime.fromisoformat(expires_at) <= timezone.now()
                except (TypeError, ValueError):
                    self.cache.delete_url(short_code)
                    cached_url = None
                    is_expired = False
                if cached_url and is_expired:
                    self.cache.delete_url(short_code)
                    raise URLExpiredException()
            if cached_url:
                logger.info(
                    "URL cache hit.",
                    extra={
                        "short_code": short_code,
                    },
                )
                return cached_url

        logger.info(
            "URL cache miss.",
            extra={
                "short_code": short_code,
            },
        )

        url = URL.objects.filter(short_code=short_code, is_active=True).first()
        if url is None:
            raise URLNotFoundException()

        if url.expires_at and url.expires_at <= timezone.now():
            raise URLExpiredException()

        cache_data = self._build_cache_data(url)

        ttl = self._calculate_cache_ttl(url.expires_at)
        if ttl > 0:
            self.cache.set_url(
                short_code=short_code,
                data=cache_data,
                ttl=ttl,
            )
        return cache_data

    def _calculate_cache_ttl(
        self,
        expires_at=None,
    ) -> int:

        ttl = settings.URL_CACHE_TTL
        if expires_at:
            remaining_seconds = int((expires_at - timezone.now()).total_seconds())

            if remaining_seconds <= 0:
                return 0

            ttl = min(
                ttl,
                remaining_seconds,
            )

        return ttl

    def get_url_list(self, user: User) -> list[dict]:
        """
        Base queryset for authenticated user's URLs.

        Filtering, searching, ordering and pagination
        are applied inside the view.
        """
        queryset = URL.objects.select_related("user").filter(
            user=user,
        )
        logger.info(
            "Fetching user URLs.",
            extra={
                "user_id": str(user.id),
            },
        )
        return queryset

    def get_users_url(self, *, user: User, url_id: str) -> dict:
        """
        Retrieve a URL belonging to the authenticated user.

        Ownership is enforced at the database-query level.
        """

        try:
            url = URL.objects.select_related("user").get(
                id=url_id,
                user=user,
            )

        except URL.DoesNotExist:
            logger.warning(
                "URL not found or user does not have access.",
                extra={
                    "user_id": str(user.id),
                    "url_id": str(url_id),
                },
            )
            raise URLNotFoundException()

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
    def update_url(self, *, user: User, url_id: str, validated_data: dict) -> dict:
        """
        Update a URL belonging to the authenticated user.
        """
        try:
            url = URL.objects.select_for_update().get(
                user=user,
                id=url_id,
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

        for field, value in validated_data.items():
            setattr(url, field, value)

        url.save(
            update_fields=[
                *validated_data.keys(),
                "updated_at",
            ]
        )

        self.cache.delete_url(url.short_code)

        logger.info(
            "URL updated successfully.",
            extra={
                "user_id": str(user.id),
                "url_id": str(url.id),
                "short_code": url.short_code,
                "updated_fields": list(validated_data.keys()),
            },
        )

        return url

    @transaction.atomic
    def delete_url(self, *, user: User, url_id: str) -> dict:
        """
        Soft delete a URL belonging to the authenticated user.
        """

        try:
            url = URL.objects.select_for_update().get(id=url_id, user=user)

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
        url.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

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
