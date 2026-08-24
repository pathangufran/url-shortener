import logging

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class ApplicationException(APIException):
    """
    Base exception for application-level errors.
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "An application error occurred."
    default_code = "application_error"


# ==========================================================
# Authentication Exceptions
# ==========================================================


class InvalidCredentialsException(ApplicationException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Invalid email or password."
    default_code = "invalid_credentials"


class AccountAlreadyExistsException(ApplicationException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "An account with this email already exists."
    default_code = "account_already_exists"


class AccountIsNotActiveException(ApplicationException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "An account with this email is not active."
    default_code = "account_is_not_active"


# ==========================================================
# URL Exceptions
# ==========================================================


class URLNotFoundException(ApplicationException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "URL not found."
    default_code = "url_not_found"


class URLExpiredException(ApplicationException):
    status_code = status.HTTP_410_GONE
    default_detail = "This URL has expired."
    default_code = "url_expired"


class DuplicateAliasException(ApplicationException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "This custom alias is already in use."
    default_code = "duplicate_alias"


class ShortCodeGenerationException(ApplicationException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Unable to generate a unique short code."
    default_code = "short_code_generation_failed"


# ==========================================================
# Analytics Exceptions
# ==========================================================


class AnalyticsNotFoundException(ApplicationException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Analytics data not found."
    default_code = "analytics_not_found"


# ==========================================================
# Global Exception Handler
# ==========================================================


def custom_exception_handler(exc, context):
    """
    Global DRF exception handler.

    Converts application and DRF exceptions into a
    consistent API error response.
    """

    response = exception_handler(
        exc,
        context,
    )
    if response is None:
        logger.exception(
            "Unhandled exception occurred.",
            exc_info=exc,
        )
        return None

    error_code = getattr(
        exc,
        "default_code",
        "error",
    )
    if isinstance(response.data, dict):
        detail = response.data.get(
            "detail",
            response.data,
        )
    else:
        detail = response.data

    response.data = {
        "success": False,
        "error": {
            "code": error_code,
            "message": detail,
        },
    }

    return response
