from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.request import Request

from serializers.register import RegisterSerializer
from serializers.response import UserResponseSerializer
from .services import AuthService

class RegisterAPIView(APIView):

    permission_classes = [AllowAny]

    def post(self,request:Request) -> Response:

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = AuthService.register_user(serializer.validated_data)

        response = UserResponseSerializer(user)

        return Response(response.data,status=status.HTTP_201_CREATED,)