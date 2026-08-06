from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request

from .serializers.register import RegisterSerializer
from .serializers.response import UserResponseSerializer
from .serializers.login import LoginSerializer
from .serializers.token import TokenResponseSerializer
from .services import AuthService
from rest_framework_simplejwt.views import TokenRefreshView

class RegisterAPIView(APIView):

    permission_classes = [AllowAny]

    def post(self,request:Request) -> Response:

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = AuthService.register_user(serializer.validated_data)

        response = UserResponseSerializer(user)

        return Response(response.data,status=status.HTTP_201_CREATED,)

class LoginAPIView(APIView):

    permission_classes = [AllowAny]

    def post(self,request):

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer_data = serializer.validated_data 

        user = AuthService.authenticate_user(
            email=serializer_data["email"],
            password=serializer_data["password"],
        )

        tokens = AuthService.generate_tokens(user)

        response = TokenResponseSerializer(tokens)

        return Response(response.data,status=status.HTTP_200_OK,)

class ProfileAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self,request):

        user = AuthService.get_profile(request.user)
        serializer = UserResponseSerializer(user)
        return Response(serializer.data,status=status.HTTP_200_OK)