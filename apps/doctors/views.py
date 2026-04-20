from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, extend_schema_view
from drf_spectacular.types import OpenApiTypes
from rest_framework import viewsets, status
from rest_framework.response import Response


from apps.common.permissions import IsAdminOrReadOnly

from .models import DoctorProfile
from .serializers import DoctorReadSerializer, DoctorSerializer

@extend_schema_view(
    list=extend_schema(
        summary="List all active doctors.",
        description="Returns a list of all available doctors working on clinic. No authentication required.",
        responses={200: DoctorReadSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                name="specialty_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filter doctors by specialty ID.",
                required=False,
            )
        ],
        tags=["Doctors"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a doctor's data",
        description="Returns the details of a single doctor by ID. No authentication required.",
        responses={
            200: DoctorReadSerializer,
            404: OpenApiResponse(description="Doctor not found."),
        },
        tags=["Doctors"],
    ),
    create=extend_schema(
        summary="Register a new doctor",
        description="Registers a new doctor and their specialties. **Admin only.**",
        request=DoctorSerializer,
        responses={
            201: DoctorReadSerializer,
            400: OpenApiResponse(description="Invalid data. Name may already exist or be missing."),
            401: OpenApiResponse(description="Authentication credentials were not provided or token has expired"),
            403: OpenApiResponse(description="User is not an Admin."),
        },
        tags=["Doctors"],
    ),
    update=extend_schema(
        summary="Update data from a registered doctor.",
        description="Fully replaces a doctor profile's data. **Admin only.**",
        responses={
            200: DoctorReadSerializer,
            400: OpenApiResponse(description="Invalid data."),
            401: OpenApiResponse(description="Authentication credentials were not provided or token has expired"),
            403: OpenApiResponse(description="User is not an Admin."),
            404: OpenApiResponse(description="Specialty not found."),
        },
        tags=["Doctors"],
    ),
    partial_update=extend_schema(
        summary="Partially update a doctor's data.",
        description="Updates one or more fields of a doctor's profile. **Admin only.**",
        responses={
            200: DoctorReadSerializer,
            400: OpenApiResponse(description="Invalid data."),
            401: OpenApiResponse(description="Authentication credentials were not provided or token has expired"),
            403: OpenApiResponse(description="User is not an Admin."),
            404: OpenApiResponse(description="Specialty not found."),
        },
        tags=["Doctors"],
    ),
    destroy=extend_schema(
        summary="Remove a doctor from the public list.",
        description="Soft deletes a registered doctor to keep integrity on patient's records. **Admin only.**",
        responses={
            204: OpenApiResponse(description="Doctor removed successfully."),
            401: OpenApiResponse(description="Authentication credentials were not provided or token has expired"),
            403: OpenApiResponse(description="User is not an Admin."),
            404: OpenApiResponse(description="Specialty not found."),
        },
        tags=["Doctors"],
    ),
)
class DoctorViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = DoctorProfile.objects.filter(is_active=True).select_related("user")
        specialty_id = self.request.query_params.get("specialty_id")
        if specialty_id:
            queryset = queryset.filter(specialties__id=specialty_id)
        return queryset
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return DoctorSerializer
        return DoctorReadSerializer
    
    def create(self, request, *args, **kwargs):
        write_serializer = DoctorSerializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        profile = write_serializer.save()
        read_serializer = DoctorReadSerializer(profile)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        write_serializer = DoctorSerializer(instance, data=request.data, partial=partial)
        write_serializer.is_valid(raise_exception=True)
        profile = write_serializer.save()
        read_serializer = DoctorReadSerializer(profile)
        return Response(read_serializer.data, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        doctor = self.get_object()
        doctor.is_active = False
        doctor.save(update_fields=["is_active"])
        return Response(
            {"detail": "Doctor successfully removed from the list."},
            status=status.HTTP_204_NO_CONTENT,
        )