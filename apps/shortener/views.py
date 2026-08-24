from django.conf import settings
from django.http import FileResponse
from django.shortcuts import redirect
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
)
from rest_framework import filters, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.services import AnalyticsService
from config.exceptions import (
    URLNotFoundException,
)

from .filters import URLFilter
from .pagination import URLPagination
from .serializers import CreateURLSerializer, UpdateURLSerializer, URLResponseSerializer
from .services import URLService
from .utils.qr import generate_qr_code
from .utils.throttling import RedirectRateThrottle, URLCreationRateThrottle


@extend_schema(
    summary="Create a short URL",
    description=(
        "Create a shortened URL with an optional custom alias and expiration date."
    ),
    request=CreateURLSerializer,
    responses={
        201: URLResponseSerializer,
        400: OpenApiResponse(description="Validation error"),
        429: OpenApiResponse(description="Rate limit exceeded"),
    },
    tags=["URL Management"],
)
class CreateURLAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [URLCreationRateThrottle]

    service = URLService()

    def post(self, request: Request) -> Response:

        serializer = CreateURLSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = self.service.create_short_url(
            user=request.user,
            long_url=serializer.validated_data["long_url"],
            expires_at=serializer.validated_data.get("expires_at"),
            custom_alias=serializer.validated_data.get("custom_alias"),
        )
        response = URLResponseSerializer(
            url,
            context={
                "request": request,
            },
        )
        return Response(response.data, status=status.HTTP_201_CREATED)


class URLListAPIView(APIView):
    """
    List URLs belonging to the authenticated user.

    Supports:
    - Pagination
    - Search
    - Filtering
    - Ordering
    """

    permission_classes = [IsAuthenticated]

    service = URLService()

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_class = URLFilter

    search_fields = [
        "long_url",
        "short_code",
    ]

    ordering_fields = [
        "created_at",
        "expires_at",
    ]

    ordering = [
        "-created_at",
    ]

    pagination_class = URLPagination

    def filter_queryset(self, queryset):
        """
        Apply filtering, searching and ordering.
        """

        for backend in self.filter_backends:
            queryset = backend().filter_queryset(
                self.request,
                queryset,
                self,
            )

        return queryset

    def get(self, request):

        queryset = self.service.get_url_list(request.user)
        queryset = self.filter_queryset(queryset)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            queryset,
            request,
        )

        serializer = URLResponseSerializer(
            page,
            many=True,
            context={
                "request": request,
            },
        )

        return paginator.get_paginated_response(serializer.data)


class URLRetrieveAPIView(APIView):
    """
    Retrieve a URL belonging to the authenticated user.
    """

    permission_classes = [IsAuthenticated]

    service = URLService()

    def get(self, request: Request, url_id: str) -> Response:

        url = self.service.get_users_url(user=request.user, url_id=url_id)
        if url is None:
            raise URLNotFoundException()

        serializer = URLResponseSerializer(
            url,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class URLUpdateAPIView(APIView):
    """
    Update a URL belonging to the authenticated user.
    """

    permission_classes = [IsAuthenticated]
    service = URLService()

    def patch(self, request: Request, url_id: str) -> Response:

        serializer = UpdateURLSerializer(
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        url = self.service.update_url(
            user=request.user, url_id=url_id, validated_data=serializer.validated_data
        )
        if url is None:
            raise URLNotFoundException()

        response_serializer = URLResponseSerializer(
            url,
            context={
                "request": request,
            },
        )
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )


class URLDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    service = URLService()

    def delete(self, request: Request, url_id: str) -> Response:

        url = self.service.delete_url(user=request.user, url_id=url_id)
        if url is None:
            raise URLNotFoundException()

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    summary="Redirect short URL",
    description=(
        "Resolve a short code and redirect the client "
        "to the original URL. Redis is checked first "
        "before falling back to PostgreSQL."
    ),
    responses={
        302: OpenApiResponse(description="Redirect to the original URL"),
        404: OpenApiResponse(description="Short URL not found"),
        410: OpenApiResponse(description="Short URL has expired"),
    },
    tags=["Redirect"],
)
class RedirectAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [RedirectRateThrottle]

    service = URLService()

    @staticmethod
    def _get_client_ip(request):
        """
        Extract the client IP address.

        X-Forwarded-For is considered because the application
        will eventually run behind Nginx. Trusted proxy handling
        will be configured during production deployment.
        """

        forwarded_for = (
            request.META.get("HTTP_X_FORWARDED_FOR")
            if settings.USE_X_FORWARDED_FOR
            else None
        )

        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR")

    def get(self, request: Request, short_code: str) -> Response:

        url = self.service.get_by_short_code(short_code)

        AnalyticsService.record_click(
            url_id=url["id"],
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT"),
            referrer=request.META.get("HTTP_REFERER"),
        )

        return redirect(
            url["long_url"],
            permanent=False,
        )


@extend_schema(
    summary="Generate URL QR code",
    description=("Generate a PNG QR code containing the short URL."),
    responses={
        200: OpenApiResponse(description="PNG QR code"),
        404: OpenApiResponse(description="URL not found"),
        429: OpenApiResponse(description="Rate limit exceeded"),
    },
    tags=["URL Management"],
)
class URLQRCodeAPIView(APIView):
    """
    Generate a QR code for a URL owned by
    the authenticated user.
    """

    permission_classes = [IsAuthenticated]

    service = URLService()

    def get(self, request: Request, url_id: str) -> Response:

        url = self.service.get_users_url(user=request.user, url_id=url_id)
        if url is None:
            raise URLNotFoundException()

        short_url = request.build_absolute_uri(f"/{url.short_code}/")

        qr_code = generate_qr_code(short_url)

        return FileResponse(
            qr_code,
            content_type="image/png",
            filename=f"{url.short_code}.png",
        )
