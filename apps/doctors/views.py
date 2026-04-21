from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, extend_schema_view
from drf_spectacular.types import OpenApiTypes
from rest_framework import viewsets, status
from rest_framework.response import Response

from apps.common.permissions import IsAdminOrReadOnly, IsAdminOrDoctorOwner

from .models import DoctorProfile, AvailabilitySchedule
from .serializers import DoctorReadSerializer, DoctorSerializer, AvailabilityScheduleSerializer

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

DOCTOR_PK_PARAMETER = OpenApiParameter(
    name="doctor_pk",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.PATH,
    description="ID of the doctor this schedule belongs to.",
    required=True,
)

@extend_schema_view(
    list=extend_schema(
        summary="List all schedule blocks for a doctor.",
        description="Returns all availability schedule blocks for a given doctor. **Admin or doctor owner only.**",
        parameters=[DOCTOR_PK_PARAMETER],
        responses={
            200: AvailabilityScheduleSerializer(many=True),
            401: OpenApiResponse(description="Authentication credentials were not provided or token has expired."),
            403: OpenApiResponse(description="User is not an Admin or the doctor owner."),
            404: OpenApiResponse(description="Doctor not found."),
        },
        tags=["Availability Schedules"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a schedule block.",
        description="Returns the details of a single schedule block by ID. **Admin or doctor owner only.**",
        parameters=[DOCTOR_PK_PARAMETER],
        responses={
            200: AvailabilityScheduleSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided or token has expired."),
            403: OpenApiResponse(description="User is not an Admin or the doctor owner."),
            404: OpenApiResponse(description="Schedule block not found."),
        },
        tags=["Availability Schedules"],
    ),
    create=extend_schema(
        summary="Add a new schedule block.",
        description="Creates a new weekly availability block for a doctor. Overlapping blocks on the same day are not allowed. The parameter `effective_until` is optional. **Admin or doctor owner only.**",
        parameters=[DOCTOR_PK_PARAMETER],
        request=AvailabilityScheduleSerializer,
        responses={
            201: AvailabilityScheduleSerializer,
            400: OpenApiResponse(description="Invalid data or overlapping schedule block."),
            401: OpenApiResponse(description="Authentication credentials were not provided or token has expired."),
            403: OpenApiResponse(description="User is not an Admin or the doctor owner."),
            404: OpenApiResponse(description="Doctor not found."),
        },
        tags=["Availability Schedules"],
    ),
    update=extend_schema(
        summary="Update a schedule block.",
        description="Fully replaces a schedule block's data. **Admin or doctor owner only.**",
        parameters=[DOCTOR_PK_PARAMETER],
        responses={
            200: AvailabilityScheduleSerializer,
            400: OpenApiResponse(description="Invalid data or overlapping schedule block."),
            401: OpenApiResponse(description="Authentication credentials were not provided or token has expired."),
            403: OpenApiResponse(description="User is not an Admin or the doctor owner."),
            404: OpenApiResponse(description="Schedule block not found."),
        },
        tags=["Availability Schedules"],
    ),
    partial_update=extend_schema(
        summary="Partially update a schedule block.",
        description="Updates one or more fields of a schedule block. **Admin or doctor owner only.**",
        parameters=[DOCTOR_PK_PARAMETER],
        responses={
            200: AvailabilityScheduleSerializer,
            400: OpenApiResponse(description="Invalid data or overlapping schedule block."),
            401: OpenApiResponse(description="Authentication credentials were not provided or token has expired."),
            403: OpenApiResponse(description="User is not an Admin or the doctor owner."),
            404: OpenApiResponse(description="Schedule block not found."),
        },
        tags=["Availability Schedules"],
    ),
    destroy=extend_schema(
        summary="Remove a schedule block.",
        description=(
            "Soft-expires a schedule block by setting an `effective_until` date. "
            "The block will no longer appear in available slots after that date. "
            "Fails if appointments exist beyond the requested date. "
            "**Admin or doctor owner only.**"
        ),
        parameters=[
            DOCTOR_PK_PARAMETER,
            OpenApiParameter(
                name="effective_until",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Date from which the schedule block will no longer be active.",
                required=True,
            )
        ],
        responses={
            204: OpenApiResponse(description="Schedule block expired successfully."),
            400: OpenApiResponse(description="effective_until date was not provided."),
            401: OpenApiResponse(description="Authentication credentials were not provided or token has expired."),
            403: OpenApiResponse(description="User is not an Admin or the doctor owner."),
            404: OpenApiResponse(description="Schedule block not found."),
            409: OpenApiResponse(description="Appointments exist beyond the requested date."),
        },
        tags=["Availability Schedules"],
    ),
)
class AvailabilityScheduleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrDoctorOwner]
    serializer_class = AvailabilityScheduleSerializer
    queryset = AvailabilitySchedule.objects.none()

    def get_queryset(self):
        doctor_pk = self.kwargs.get("doctor_pk")
        if not doctor_pk:
            return AvailabilitySchedule.objects.none()
        return AvailabilitySchedule.objects.filter(doctor__pk=doctor_pk).order_by("day_of_week")
    
    def get_doctor(self):
        return DoctorProfile.objects.get(pk=self.kwargs["doctor_pk"])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.kwargs.get("doctor_pk"):
            context["doctor"] = self.get_doctor()
        return context

    def create(self, request, *args, **kwargs):
        doctor = self.get_doctor()
        serializer = AvailabilityScheduleSerializer(
            data=request.data,
            context={"doctor": doctor, "request":request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(doctor=doctor)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        schedule = self.get_object()
        effective_until = request.query_params.get("effective_until")

        if not effective_until:
            return Response(
                {"detail": "effective_until date is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        has_future_appointments = schedule.doctor.appointments.filter(
            date__gt=effective_until,
            status="scheduled",
        ).exists()

        if has_future_appointments:
            return Response(
                {"detail": "Appointments exist beyond the requested date."},
                status=status.HTTP_409_CONFLICT,
            )

        schedule.effective_until = effective_until
        schedule.save(update_fields=["effective_until"])
        return Response(
            {"detail": f"Schedule block will no longer accept bookings after {effective_until}."},
            status=status.HTTP_204_NO_CONTENT,
        )
