from rest_framework import status,filters
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services import URLService 
from .pagination import URLPagination
from .filters import URLFilter
from .serializers import (
    CreateURLSerializer,
    URLResponseSerializer,
    UpdateURLSerializer
)
from django.http import Http404,HttpResponseGone
from django.shortcuts import redirect
from django.views import View
from django_filters.rest_framework import DjangoFilterBackend
from apps.analytics.services import AnalyticsService
from .utils.throttling import URLCreationRateThrottle,RedirectRateThrottle

class CreateURLAPIView(APIView):

    permission_classes = [IsAuthenticated]
    throttle_classes = [URLCreationRateThrottle]

    service = URLService()

    def post(self,request:Request) -> Response:

        serializer = CreateURLSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = self.service.create_short_url(
            user=request.user,
            user=request.user,
            long_url=serializer.validated_data["long_url"],
            expires_at=serializer.validated_data.get("expires_at"),
            custom_alias=serializer.validated_data.get("custom_alias"),
        )
        response = URLResponseSerializer(url,context={"request": request,},)
        return Response(response.data,status=status.HTTP_201_CREATED)


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

    search_fields = ["long_url","short_code",]

    ordering_fields = ["created_at","expires_at",]

    ordering = ["-created_at",]

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

        queryset = self.service.list_urls(request.user)
        queryset = self.filter_queryset(queryset)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset,request,)

        serializer = URLResponseSerializer(
            page,many=True,
            context={"request": request,},
        )

        return paginator.get_paginated_response(
            serializer.data,
            status=status.HTTP_200_OK
        )

class URLRetrieveAPIView(APIView):
    """
    Retrieve a URL belonging to the authenticated user.
    """

    permission_classes = [IsAuthenticated]

    service = URLService()

    def get(self,request:Request,url_id:str) -> Response:

        url = self.service.get_users_url(
            user=request.user,
            url_id=url_id
        )
        if url is None:
            raise Http404("URL not found.")
        
        serializer = URLResponseSerializer(url,context={"request": request,},)

        return Response(serializer.data,status=status.HTTP_200_OK,)

class URLUpdateAPIView(APIView):
    """
    Update a URL belonging to the authenticated user.
    """

    permission_classes = [IsAuthenticated]
    service = URLService()

    def patch(self,request:Request,url_id:str) -> Response:

        serializer = UpdateURLSerializer(
            data=request.data,partial=True,
        )
        serializer.is_valid(raise_exception=True)
        url = self.service.update_url(
            user=request.user,
            url_id=url_id,
            validated_data=serializer.validated_data
        )
        if url is None:
            raise Http404(
                "URL not found."
            )
        response_serializer = URLResponseSerializer(
            url,
            context={"request": request,},
        ) 
        return Response(
            response_serializer.data,status=status.HTTP_200_OK,
        )

class URLDeleteAPIView(APIView):

    permission_classes = [IsAuthenticated]

    service = URLService()

    def delete(self,request:Request,url_id:str) -> Response:

        url = self.service.delete_url(
            user=request.user,
            url_id=url_id
        )
        if url is None:
            raise Http404("URL not found.")

        return Response(status=status.HTTP_204_NO_CONTENT)


class RedirectAPIView(View):

    throttle_classes = [URLCreationRateThrottle]

    service = URLService()

    @staticmethod
    def _get_client_ip(request):
        """
        Extract the client IP address.

        X-Forwarded-For is considered because the application
        will eventually run behind Nginx. Trusted proxy handling
        will be configured during production deployment.
        """

        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR")

    def get(self,request:Request,short_code:str) -> Response:

        url = self.service.get_by_short_code(short_code)

        if url is None:
            raise Http404("Short URL not found.")
        
        if url == "expired":
            return HttpResponseGone("This URL has expired.")

        AnalyticsService.record_click(
            url_id=url.id,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT"),
            referrer=request.META.get("HTTP_REFERER"),
        )

        return redirect(url.long_url,permanent=False,)