from rest_framework import status,filters
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services import URLService 
from .pagination import URLPagination
from .filters import URLFilter
from .serializers import CreateURLSerializer,URLResponseSerializer
from django.http import Http404,HttpResponseGone
from django.shortcuts import redirect
from django.views import View
from django_filters.rest_framework import DjangoFilterBackend

class CreateURLAPIView(APIView):

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

    def filter_queryset(self,queryset:dict) -> list[dict]:
        """
        Apply filtering, searching and ordering manually.
        """

        for backend in self.filter_backends:
            queryset = backend().filter_queryset(
                self.request,queryset,self,
            )

            return queryset

    def get(self,request:Request) -> Response:

        queryset = self.service.get_url_list(request.user)
        queryset = self.filter_queryset(queryset) 
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset,request)
        serializer = URLResponseSerializer(
            page,many=True,context={"request": request,},
        )

        return paginator.get_paginated_response(serializer.data)

    def post(self,request:Request) -> Response:

        serializer = CreateURLSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = self.service.create_short_url(
            user=request.user,
            **serializer.validated_data,
        )
        response = URLResponseSerializer(url,context={"request": request,},)
        return Response(response.data,status=status.HTTP_201_CREATED)


class RedirectAPIView(View):

    service = URLService()

    def get(self,request:Request,short_code:str) -> Response:

        url = self.service.get_by_short_code(short_code)

        if url is None:
            raise Http404("Short URL not found.")
        
        if url == "expired":
            return HttpResponseGone("This URL has expired.")

        return redirect(url.long_url,permanent=False,)