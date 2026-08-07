from rest_framework import status
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services import URLService 
from .serializers import CreateURLSerializer,URLResponseSerializer

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
        