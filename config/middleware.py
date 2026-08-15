import logging
import time
import uuid

logger = logging.getLogger("django.request")

class RequestLoggingMiddleware:
    """
    Logs incoming HTTP requests with request ID,
    status code and response duration.
    """

    def __init__(self,get_response):
        self.get_response = get_response

    def __call__(self,request):
        if request.path in {
            "/health/",
            "/health/ready/",
        }:
            return self.get_response(request)
        
        request_id = str(uuid.uuid4())
        request.request_id = request_id
        start_time = time.perf_counter()
        response = None
        try:
            response = self.get_response(request)
            response["X-Request-ID"] = request_id
            return response

        finally:
            duration = (time.perf_counter() - start_time)
            duration_ms = round(
                duration * 1000,
                2,
            )
            status_code = (
                response.status_code 
                if response is not None
                else 500
            )
            logger.info(
                "HTTP request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "user_id": (
                        str(request.user.id)
                        if getattr(
                            request,
                            "user",
                            None,
                        )
                        and request.user.is_authenticated
                        else None
                    ),
                },
            )