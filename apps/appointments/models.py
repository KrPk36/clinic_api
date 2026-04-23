from django.db import models

from apps.doctors.models import DoctorProfile
from apps.user.models import PatientProfile


SLOT_DURATION_MINUTES = 30

class Appointment(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"

    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="appointments_as_patient",
    )
    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name="appointments",
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevents double-booking at the DB constraint level
        unique_together = ("doctor", "date", "start_time")

    def __str__(self):
        return f"{self.patient.user.get_full_name()} with Dr. {self.doctor.user.get_full_name()} on {self.date} at {self.start_time}"