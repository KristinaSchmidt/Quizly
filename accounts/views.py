from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .functions import (
    blacklist_refresh_token,
    clear_auth_cookies,
    set_auth_cookie,
)
from .serializers import RegistrationSerializer


class RegisterView(APIView):
    """Register a new user."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "User created successfully!"},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Validate credentials and store JWTs in HttpOnly cookies."""

    permission_classes = [AllowAny]

    def post(self, request):
        user = authenticate(
            username=request.data.get("username"),
            password=request.data.get("password"),
        )
        if user is None:
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        refresh = RefreshToken.for_user(user)
        return self.login_response(user, refresh)

    @staticmethod
    def login_response(user, refresh):
        response = Response({
            "detail": "Login successfully!",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },
        })
        set_auth_cookie(response, "access_token", str(refresh.access_token), 900)
        set_auth_cookie(response, "refresh_token", str(refresh), 604800)
        return response


class LogoutView(APIView):
    """Blacklist the refresh token and remove authentication cookies."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.COOKIES.get("refresh_token")
        blacklist_refresh_token(token)
        response = Response({
            "detail": (
                "Log-Out successfully! All Tokens will be deleted. "
                "Refresh token is now invalid."
            )
        })
        clear_auth_cookies(response)
        return response


class TokenRefreshCookieView(APIView):
    """Create a new access token from the refresh-token cookie."""

    permission_classes = [AllowAny]

    def post(self, request):
        token = request.COOKIES.get("refresh_token")
        if not token:
            return self.invalid_response()
        try:
            access_token = str(RefreshToken(token).access_token)
        except TokenError:
            return self.invalid_response()
        return self.success_response(access_token)

    @staticmethod
    def success_response(access_token):
        response = Response({"detail": "Token refreshed"})
        set_auth_cookie(response, "access_token", access_token, 900)
        return response

    @staticmethod
    def invalid_response():
        return Response(
            {"detail": "Refresh token invalid or missing."},
            status=status.HTTP_401_UNAUTHORIZED,
        )