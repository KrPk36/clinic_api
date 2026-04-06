# apps/common/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError, AuthenticationFailed
from drf_spectacular.extensions import OpenApiAuthenticationExtension


class JWTSoftAuthentication(JWTAuthentication):
    """
    Behaves like JWTAuthentication but does not raise an error when the token
    is invalid or expired. Instead it returns None, letting the request
    continue as an anonymous user.

    This allows permission classes like IsAdminOrReadOnly to grant access
    to public endpoints even when the client sends an expired token.
    """

    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except (InvalidToken, TokenError, AuthenticationFailed):
            return None

class JWTSoftAuthenticationScheme(OpenApiAuthenticationExtension):
    """
    Tells drf-spectacular how to document JWTSoftAuthentication.
    Maps it to the same OpenAPI security scheme as the standard JWTAuthentication.
    """
    target_class = "apps.common.authentication.JWTSoftAuthentication"
    name = "jwtAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": (
                "JWT authentication.\n\n"
                "Obtain a token pair via `POST /api/auth/login/`.\n\n"
                "Enter only the access token — the `Bearer` prefix is added automatically."
            ),
        }