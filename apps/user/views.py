from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import EmailTokenObtainPairSerializer, TokenResponseSerializer, PatientCreateSerializer, PatientReadSerializer

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
        tags=["Auth"],
    )
)
class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer

@extend_schema_view(
    post=extend_schema(
        summary="Self register as a patient",
        description=(
            "Register a new user based on the provided data.\n\n"
            "Users created through this endpoint are always registered as \"Patient\"."
        ),
        request=PatientCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=PatientReadSerializer,
                description="Patient successfully registered."
            ),
            400: OpenApiResponse(description="Invalid data."),
        },
        tags=["Auth"],
    )
)
class PatientRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PatientCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        read_serializer = PatientReadSerializer(profile.user)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED,)