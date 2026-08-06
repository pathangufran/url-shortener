import logging
from django.db import transaction
from django.contrib.auth import get_user_model

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
        