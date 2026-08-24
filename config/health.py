import logging
from django.db import connection
from django.http import JsonResponse
from apps.shortener.utils.redis_client import RedisCache

logger = logging.getLogger(__name__)

def health_check(request):
    """
    Liveness check.

    Verifies that the Django application is running.
    """

    return JsonResponse(
        {
            "status": "healthy",
        },
        status=200,
    )

def readiness_check(request):
    """
    Readiness check.

    Verifies that required infrastructure
    is available before serving traffic.
    """

    checks = {
        "database": False,
        "redis": False,
    }

    # ------------------------------------------------------
    # PostgreSQL
    # ------------------------------------------------------

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        checks["database"] = True

    except Exception:
        logger.exception("Database readiness check failed.")

    # ------------------------------------------------------
    # Redis
    # ------------------------------------------------------

    try:
        redis_client = RedisCache()
        redis_client.client.ping()
        checks["redis"] = True

    except Exception:
        logger.exception("Redis readiness check failed.")

    # ------------------------------------------------------
    # Overall status
    # ------------------------------------------------------

    is_ready = all(checks.values())

    response_data = {
        "status": ("ready" if is_ready else "not_ready"),
        "checks": checks,
    }

    return JsonResponse(
        response_data,
        status=200 if is_ready else 503,
    )
