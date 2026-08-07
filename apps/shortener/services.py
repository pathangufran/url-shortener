import secrets
import string
from .models import URL
from django.conf import settings

BASE62_ALPHABET = (string.ascii_letters + string.digits)

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
            if not URL.objects.filter(code=code).exists():
                return code


