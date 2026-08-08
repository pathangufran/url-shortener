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

class CreateURLAPIView(APIView):

    permission_classes = [IsAuthenticated]

    service = URLService()

    def post(self,request:Request) -> Response:

        serializer = CreateURLSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = self.service.create_short_url(
            user=request.user,
            **serializer.validated_data,
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


class RedirectAPIView(View):

    service = URLService()

    def get(self,request:Request,short_code:str) -> Response:

        url = self.service.get_by_short_code(short_code)

        if url is None:
            raise Http404("Short URL not found.")
        
        if url == "expired":
            return HttpResponseGone("This URL has expired.")

        return redirect(url.long_url,permanent=False,)