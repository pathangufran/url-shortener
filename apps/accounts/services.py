import logging
from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken
from config.exceptions import (
    AccountAlreadyExistsException,
    AccountIsNotActiveException,
    InvalidCredentialsException,
)

User = get_user_model()

logger = logging.getLogger(__name__)

class AuthService:
    @transaction.atomic
    @staticmethod
    def register_user(
        data: dict,
    ) -> User:

        logger.info(
            "Creating new user",
            extra={
                "email": data["email"],
            },
        )
        try:
            user = User.objects.create_user(
                email=data["email"],
                password=data["password"],
                first_name=data["first_name"],
                last_name=data["last_name"],
            )
            logger.info(
                "User created successfully",
                extra={
                    "user_id": str(user.id),
                    "email": user.email,
                },
            )

            return user

        except Exception as exc:
            logger.exception("User registration failed")
            # The serializer pre-check is only advisory; a unique constraint is
            # still the authority under concurrent registration requests.
            from django.db import IntegrityError

            if isinstance(exc, IntegrityError):
                raise AccountAlreadyExistsException() from exc
            raise

    @staticmethod
    def authenticate_user(email: str, password: str):

        user = authenticate(username=email, password=password)

        if user is None:
            logger.warning(
                "Login failed",
                extra={
                    "email": email,
                },
            )
            raise InvalidCredentialsException()

        if not user.is_active:
            logger.warning(
                "Inactive user login attempt",
                extra={
                    "user_id": str(user.id),
                },
            )

            raise AccountIsNotActiveException()

        return user

    @staticmethod
    def generate_tokens(user):
        logger.info(
            "User login successful",
            extra={
                "user_id": str(user.id),
                "email": user.email,
            },
        )

        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

    @staticmethod
    def get_profile(user):

        return user
