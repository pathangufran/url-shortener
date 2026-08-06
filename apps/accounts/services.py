import logging
from django.db import transaction
from django.contrib.auth import get_user_model,authenticate
from django.contrib.auth.models import update_last_login
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

logger = logging.getLogger(__name__)

class AuthService:

    @transaction.atomic
    @staticmethod
    def register_user(data: dict,) -> User:

        logger.info("Creating new user",extra={"email": data["email"],},)
        try:
            user = User.objects.create_user(
                email=data["email"],
                password=data["password"],
                first_name=data["first_name"],
                last_name=data["last_name"],
            )
            logger.info(
                "User created successfully",
                extra={"user_id": str(user.id),"email": user.email,},
            )

            return user
        
        except Exception:

            logger.exception("User registration failed")

            raise

    @staticmethod
    def authenticate_user(email:str,password:str):

        user = authenticate(username=email,password=password)

        if user is None:
            logger.warning("Login failed",extra={"email": email,},)
            raise AuthenticationFailed("Invalid email or password.")

        if not user.is_active:

            logger.warning(
                "Inactive user login attempt",
                extra={"user_id": str(user.id),},
            )

            raise AuthenticationFailed("User account is inactive.")

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
        update_last_login(None,user,)

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

    @staticmethod
    def get_profile(user):

        return user