from django.urls import path
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiExample
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .views import EmailTokenObtainPairView, PatientRegisterView, UserProfileView

# Patch TokenRefreshView
extend_schema_view(
    post=extend_schema(
        summary="Refresh access token",
        description=(
            "Takes a valid refresh token and returns a new access token. "
            "Refresh tokens are valid for 7 days by default."
        ),
        tags=["Auth"],
        responses={
            200: OpenApiResponse(description="New access token returned successfully"),
            401: OpenApiResponse(description="Refresh token is invalid or expired"),
        },
    )
)(TokenRefreshView)

# Patch TokenVerifyView
extend_schema_view(
    post=extend_schema(
        summary="Verify token",
        description="Checks whether a given token (access or refresh) is still valid.",
        tags=["Auth"],
        responses={
            200: OpenApiResponse(description="Token is valid"),
            401: OpenApiResponse(description="Token is invalid or expired"),
        },
    )
)(TokenVerifyView)

me_view = UserProfileView.as_view({
    "get":"retrieve",
    "patch":"partial_update"
})

urlpatterns = [
    path('login/', EmailTokenObtainPairView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('register/', PatientRegisterView.as_view(), name="patient_register"),
    path('me/', me_view, name="me"),
]