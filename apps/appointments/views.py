from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from rest_framework import viewsets, status, mixins
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.common.permissions import AppointmentsPermission

from .models import Appointment
from .serializers import AppointmentReadSerializer, AppointmentCreateSerializer, AppointmentCancelSerializer, AppointmentCompleteSerializer

@extend_schema_view(
    list=extend_schema(
        summary="List all appointments.",
        description="Returns a list of all own appointments for Patients and Doctors. List all registered appointments if user is Admin. **Must be logged in**",
        responses={
            200: AppointmentReadSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided or token has expired."),
        },
        tags=["Appointments"],
    ),
    retrieve=extend_schema(
        summary="Retrieve an appointment's data",
        description="Returns the data of a single appointment by ID. User has to be either Patient or Doctor registered in the appointment to see the data. Admin can retrieve any appointment.",
        responses={
            200: AppointmentReadSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided or token has expired."),
            403: OpenApiResponse(description="User is not an Admin or the owner of the appointment."),
        },
        tags=["Appointments"],
    ),
    create=extend_schema(
        summary="Book a new appointment.",
        description="Books an appointmet for the logged in user. Start time for the appointment must start on the hour or half hour (e.g. 09:00 or 09:30). **Patient only**.",
        request=AppointmentCreateSerializer,
        responses={
            201: AppointmentReadSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided or token has expired."),
            403: OpenApiResponse(description="User is not a Patient."),
        },
        tags=["Appointments"],
    ),
    cancel=extend_schema(
        summary="Cancel an appointment.",
        description="Update an appointment's status by ID as `Cancelled`. **Must be Patient and own the appointment.**",
        responses={
            200: AppointmentReadSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided or token has expired."),
            403: OpenApiResponse(description="User is not a Patient."),
            404: OpenApiResponse(description="No Appointment with matching ID belongs to user."),
        },
        tags=["Appointments"],
    ),
    complete=extend_schema(
        summary="Complete an appointment.",
        description="Update an appointment's status by ID as `Completed`. **Must be Admin or Doctor and own the appointment.**",
        responses={
            200: AppointmentReadSerializer,
            401: OpenApiResponse(description="Authentication credentials were not provided or token has expired."),
            403: OpenApiResponse(description="User is not a Doctor."),
            404: OpenApiResponse(description="No Appointment with matching ID belongs to user."),
        },
        tags=["Appointments"],
    ),
)
class AppointmentViewSet(mixins.CreateModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.ListModelMixin,
                         GenericViewSet):
    permission_classes = [AppointmentsPermission]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Appointment.objects.all()
        if hasattr(self.request.user, "doctor_profile"):
            return Appointment.objects.filter(doctor=user.doctor_profile).order_by("date")
        if hasattr(self.request.user, "patient_profile"):
            return Appointment.objects.filter(patient=user.patient_profile).order_by("date")
        return Appointment.objects.none()
    
    def get_serializer_class(self):
        if self.action == "create":
            return AppointmentCreateSerializer
        if self.action == "cancel":
            return AppointmentCancelSerializer
        if self.action == "complete":
            return AppointmentCompleteSerializer
        return AppointmentReadSerializer
        
    def create(self, request, *args, **kwargs):
        patient = self.request.user.patient_profile
        write_serializer = AppointmentCreateSerializer(
            data=request.data,
            context={"patient":patient}
        )
        write_serializer.is_valid(raise_exception=True)
        appointment = write_serializer.save()
        read_serializer = AppointmentReadSerializer(appointment)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=["patch"], url_path="cancel")
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        patch_serializer = AppointmentCancelSerializer(
            context={"pk":appointment.pk}
        )
        appointment = patch_serializer.cancel()
        read_serializer = AppointmentReadSerializer(appointment)
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["patch"], url_path="complete")
    def complete(self, request, pk=None):
        appointment = self.get_object()
        patch_serializer = AppointmentCompleteSerializer(
            data=request.data,
            context={"pk":appointment.pk}
        )
        patch_serializer.is_valid(raise_exception=True)
        appointment = patch_serializer.complete()
        read_serializer = AppointmentReadSerializer(appointment)
        return Response(read_serializer.data, status=status.HTTP_200_OK)
