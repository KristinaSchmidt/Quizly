from django.conf import settings
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken


def set_auth_cookie(response, name, value, max_age):
    """Set one JWT cookie using the project's security configuration."""
    response.set_cookie(
        name,
        value,
        max_age=max_age,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
    )


def clear_auth_cookies(response):
    """Remove both authentication cookies from the browser."""
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")


def blacklist_refresh_token(token):
    """Blacklist a refresh token when it is valid."""
    if not token:
        return
    try:
        RefreshToken(token).blacklist()
    except TokenError:
        pass