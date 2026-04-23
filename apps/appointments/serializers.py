from django.db import transaction
from django.db.models import Q
from rest_framework import serializers
import datetime

from apps.doctors.models import DoctorProfile, AvailabilitySchedule

from .models import Appointment, SLOT_DURATION_MINUTES

class AppointmentReadSerializer(serializers.ModelSerializer):
    doctors_name = serializers.CharField(source="doctor.__str__")
    patients_name = serializers.CharField(source="patient.__str__")

    class Meta:
        model = Appointment
        fields = ["id", "doctors_name", "patients_name", "date", "start_time", "end_time", "status"]

def validate_slot_boundary(value):
    if value.minute not in (0, 30) or value.second != 0:
        raise serializers.ValidationError(
            "Appointments must start on the hour or half hour (e.g. 09:00 or 09:30)."
        )
    return value

def get_last_valid_slot(end_time):
    d = datetime.datetime.combine(datetime.date.today(), end_time)
    return (d - datetime.timedelta(minutes=30)).time()

def get_end_time(start_time):
    d = datetime.datetime.combine(datetime.date.today(), start_time)
    return (d + datetime.timedelta(minutes=SLOT_DURATION_MINUTES)).time()

class AppointmentCreateSerializer(serializers.Serializer):
    doctor_id = serializers.PrimaryKeyRelatedField(queryset=DoctorProfile.objects.all())
    date = serializers.DateField()
    start_time = serializers.TimeField(
        validators=[validate_slot_boundary],
        help_text="Format: HH:MM:SS. Must be on the hour or half hour.",
    )

    def validate(self, data):
        doctor = data["doctor_id"]
        date = data["date"]
        start_time = data["start_time"]

        if datetime.datetime.combine(date, start_time) < datetime.datetime.now():
            raise serializers.ValidationError(
                "You cannot book an appointment for a past date and time."
            )
        
        available_schedule = AvailabilitySchedule.objects.filter(
            doctor=doctor,
            day_of_week=date.weekday(),
            start_time__lte=start_time,
            end_time__gt=start_time,
        ).filter(
            Q(effective_until__isnull=True) | Q(effective_until__gte=date)
        ).first()

        if not available_schedule:
            raise serializers.ValidationError(
                "The doctor has no availability on this day and time."
            )
        
        last_valid_slot = get_last_valid_slot(available_schedule.end_time)
        if start_time > last_valid_slot:
            raise serializers.ValidationError(
                "You must book an appointment during valid schedule."
            )

        already_booked = Appointment.objects.filter(
            doctor=doctor,
            date=date,
            start_time=start_time,
            status=Appointment.Status.SCHEDULED
        ).exists()

        if already_booked:
            raise serializers.ValidationError(
                "This slot is already booked"
            )
        return data

    @transaction.atomic
    def create(self, validated_data):
        patient = self.context.get("patient")
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=validated_data["doctor_id"],
            date=validated_data["date"],
            start_time=validated_data["start_time"],
            end_time=get_end_time(validated_data["start_time"]),
            status=Appointment.Status.SCHEDULED
        )
        return appointment

class AppointmentPatchSerializer(serializers.Serializer):
    def cancel(self):
        pk = self.context.get("pk")
        appointment = Appointment.objects.get(pk=pk)

        if appointment.status != Appointment.Status.SCHEDULED:
            raise serializers.ValidationError(
                "Only scheduled appointments can be cancelled."
            )
        if appointment.date < datetime.date.today():
            raise serializers.ValidationError(
                "Cannot cancel a past appointment."
            )

        appointment.status = Appointment.Status.CANCELLED
        appointment.save(update_fields=["status"])
        return appointment

    def complete(self):
        pk = self.context.get("pk")
        appointment = Appointment.objects.get(pk=pk)

        if appointment.status != Appointment.Status.SCHEDULED:
            raise serializers.ValidationError(
                "Only scheduled appointments can be marked as completed."
            )
        if appointment.date > datetime.date.today():
            raise serializers.ValidationError(
                "Cannot complete a future appointment."
            )

        appointment.status = Appointment.Status.COMPLETED
        appointment.save(update_fields=["status"])
        return appointment
    