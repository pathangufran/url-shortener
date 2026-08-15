import logging
from django.http import Http404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    URLAnalyticsResponseSerializer,
    AnalyticsFilterSerializer,
    ClickEventSerializer,
    ClickEventFilterSerializer
)
from .services import AnalyticsService
from apps.shortener.utils.throttling import AnalyticsRateThrottle
from drf_spectacular.utils import (
    OpenApiResponse,
    OpenApiParameter,
    OpenApiTypes,
    extend_schema
)
from config.exceptions import (
    URLNotFoundException
)

logger = logging.getLogger(__name__)

@extend_schema(
    summary="Get URL analytics",
    description=(
        "Return aggregated click analytics for a URL. "
        "Optional start_date and end_date filters can "
        "be used to restrict the reporting period."
    ),
    responses={
        200: URLAnalyticsResponseSerializer,
        404: OpenApiResponse(
            description="URL not found"
        ),
        429: OpenApiResponse(
            description="Rate limit exceeded"
        ),
    },
    tags=["Analytics"],
)
class URLAnalyticsAPIView(APIView):
    """
    Return analytics for a URL owned by the
    authenticated user.

    Supports optional:
    - start_date
    - end_date
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    service = AnalyticsService()

    def get(self,request:Request,url_id:str) -> Response:

        filter_serializer = AnalyticsFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)    

        analytics = self.service.get_url_analytics(
            user=request.user,
            id=url_id,
            **filter_serializer.validated_data,
        )
        
        if analytics is None:
            raise URLNotFoundException()

        serializer = URLAnalyticsResponseSerializer(analytics)
        logger.info(
            "URL analytics API request completed.",
            extra={
                "user_id": str(request.user.id),
                "url_id": str(url_id),
                "start_date": str(
                    filter_serializer.validated_data.get("start_date")
                ),
                "end_date": str(
                    filter_serializer.validated_data.get("end_date")
                ),
            },
        )

        return Response(serializer.data,status=status.HTTP_200_OK,)


@extend_schema(
    summary="List URL click events",
    description=(
        "Return paginated click events for a URL "
        "owned by the authenticated user."
    ),
    parameters=[
        OpenApiParameter(
            name="start_date",
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
        ),
        OpenApiParameter(
            name="end_date",
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
        ),
        OpenApiParameter(
            name="browser",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
        ),
        OpenApiParameter(
            name="device",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
        ),
        OpenApiParameter(
            name="country",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
        ),
        OpenApiParameter(
            name="ordering",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
        ),
        OpenApiParameter(
            name="page",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
        ),
        OpenApiParameter(
            name="page_size",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
        ),
    ],
    responses={
        200: ClickEventSerializer(many=True),
        404: OpenApiResponse(
            description="URL not found"
        ),
        429: OpenApiResponse(
            description="Rate limit exceeded"
        ),
    },
    tags=["Analytics"],
)
class URLClickEventsAPIView(APIView):
    """
    Return raw click events for a URL owned by
    the authenticated user.

    Supports:
    - Pagination
    - Date filtering
    - Browser filtering
    - Device filtering
    - Country filtering
    - Ordering
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [AnalyticsRateThrottle]

    service = AnalyticsService()

    page_size = 20
    max_page_size = 100

    def get(self,request:Request,url_id:str) -> Response:
        filter_serializer = ClickEventFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)

        queryset = self.service.get_click_events(
            user=request.user,
            url_id=url_id,
            ordering=request.query_params.get("ordering","-clicked_at",),
            **filter_serializer.validated_data,
        )
        if queryset is None:
            raise URLNotFoundException()
        
        page = self._paginate_queryset(queryset,request,)
        serializer = ClickEventSerializer(page["results"],many=True,)

        response_data = {
            "count": page["count"],
            "next": page["next"],
            "previous": page["previous"],
            "results": serializer.data,
        }
        logger.info(
            "URL click events API request completed.",
            extra={
                "user_id": str(request.user.id),
                "url_id": str(url_id),
                "page": page["page"],
                "page_size": page["page_size"],
            },
        )

        return Response(response_data,status=status.HTTP_200_OK,)

    def _paginate_queryset(self,queryset:list[dict],request:Request,) -> Response:
        """
        Paginate queryset without introducing another
        pagination file.
        """

        try:
            page = int(request.query_params.get("page",1,))

        except (TypeError, ValueError):
            page = 1

        try:
            page_size = int(request.query_params.get(
                    "page_size",
                    self.page_size,
                )
            )

        except (TypeError, ValueError):
            page_size = self.page_size

        page = max(page, 1)
        page_size = min(max(page_size, 1),self.max_page_size,)

        offset = (page - 1) * page_size

        total_count = queryset.count()

        results = queryset[offset:offset + page_size]

        next_page = (page + 1 if offset + page_size < total_count else None)

        previous_page = (page - 1 if page > 1 else None)

        return {
            "count": total_count,
            "page": page,
            "page_size": page_size,
            "next": next_page,
            "previous": previous_page,
            "results": results,
        }

