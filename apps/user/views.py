from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import EmailTokenObtainPairSerializer, TokenResponseSerializer

@extend_schema_view(
    post=extend_schema(
    summary="Obtain JWT token pair",
    description=(
        "Authenticates a user with email and password.\n\n"
        "Returns an **access token** (short-lived) and a **refresh token** (long-lived)."
    ),
    request=EmailTokenObtainPairSerializer,
    responses={
        200: OpenApiResponse(
            response=TokenResponseSerializer,
            description="Succesfully generated tokens."
        ),
        400: OpenApiResponse(description="Invalid credentials."),
    },
    tags=["Auth"],)
)
class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer