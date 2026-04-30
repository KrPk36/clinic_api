from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .serializers import *

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
                response=UserProfileReadSerializer,
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
        read_serializer = UserProfileReadSerializer(profile.user)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED,)

@extend_schema_view(
    retrieve=extend_schema(
        summary="Retrieve own profile.",
        description="Returns the profile information of the currently authenticated user.",
        responses={
            200: UserProfileReadSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided or token has expired."),
        },
        tags=["Auth"],
    ),
    partial_update=extend_schema(
        summary="Update own profile.",
        description="Updates one or more fields of the authenticated user's profile. Email and role cannot be changed.",
        request=UserProfileUpdateSerializer,
        responses={
            200: UserProfileReadSerializer,
            400: OpenApiResponse(description="Invalid data."),
            401: OpenApiResponse(description="Authentication credentials were not provided or token has expired."),
        },
        tags=["Auth"],
    ),
)
class UserProfileView(mixins.RetrieveModelMixin, 
                      mixins.UpdateModelMixin, 
                      GenericViewSet):
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.action == "partial_update":
            return UserProfileUpdateSerializer
        return UserProfileReadSerializer
    
    def update(self, request, *args, **kwargs):
        if not kwargs.get("partial", False):
            return Response(
                {"detail":"Method not allowed. Use PATCH for partial updates."},
                status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        write_serializer = UserProfileUpdateSerializer(
            self.request.user,
            data=request.data,
            partial=True,
            context={"request":request},
        )
        write_serializer.is_valid(raise_exception=True)
        write_serializer.save()
        read_serializer = UserProfileReadSerializer(self.request.user)
        return Response(read_serializer.data, status=status.HTTP_200_OK)
        