from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import viewsets

from apps.common.permissions import IsAdminOrReadOnly

from .models import Specialty
from .serializers import SpecialtySerializer

@extend_schema_view(
    list=extend_schema(
        summary="List all specialties",
        description="Returns a list of all available medical specialties. No authentication required.",
        responses={200: SpecialtySerializer(many=True)},
        tags=["Specialties"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a specialty",
        description="Returns the details of a single specialty by ID. No authentication required.",
        responses={
            200: SpecialtySerializer,
            404: OpenApiResponse(description="Specialty not found."),
        },
        tags=["Specialties"],
    ),
    create=extend_schema(
        summary="Create a specialty",
        description="Creates a new medical specialty. **Admin only.**",
        responses={
            201: SpecialtySerializer,
            400: OpenApiResponse(description="Invalid data. Name may already exist or be missing."),
            401: OpenApiResponse(description="Authentication credentials were not provided or token has expired"),
            403: OpenApiResponse(description="User is not an Admin."),
        },
        tags=["Specialties"],
    ),
    update=extend_schema(
        summary="Update a specialty",
        description="Fully replaces a specialty's data. **Admin only.**",
        responses={
            200: SpecialtySerializer,
            400: OpenApiResponse(description="Invalid data."),
            401: OpenApiResponse(description="Authentication credentials were not provided or token has expired"),
            403: OpenApiResponse(description="User is not an Admin."),
            404: OpenApiResponse(description="Specialty not found."),
        },
        tags=["Specialties"],
    ),
    partial_update=extend_schema(
        summary="Partially update a specialty",
        description="Updates one or more fields of a specialty. **Admin only.**",
        responses={
            200: SpecialtySerializer,
            400: OpenApiResponse(description="Invalid data."),
            401: OpenApiResponse(description="Authentication credentials were not provided or token has expired"),
            403: OpenApiResponse(description="User is not an Admin."),
            404: OpenApiResponse(description="Specialty not found."),
        },
        tags=["Specialties"],
    ),
    destroy=extend_schema(
        summary="Delete a specialty",
        description="Permanently deletes a specialty. **Admin only.**",
        responses={
            204: OpenApiResponse(description="Specialty deleted successfully."),
            401: OpenApiResponse(description="Authentication credentials were not provided or token has expired"),
            403: OpenApiResponse(description="User is not an Admin."),
            404: OpenApiResponse(description="Specialty not found."),
        },
        tags=["Specialties"],
    ),
)
class SpecialtyViewSet(viewsets.ModelViewSet):
    queryset = Specialty.objects.all().order_by("name")
    serializer_class = SpecialtySerializer
    permission_classes = [IsAdminOrReadOnly]