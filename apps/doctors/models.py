from django.db import models
from django.conf import settings

from apps.common.models import GenderChoices

class DoctorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_profile",
    )
    gender = models.CharField(max_length=1, choices=GenderChoices.choices)
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    specialties = models.ManyToManyField(
        "specialties.Specialty",
        related_name="doctors",
        blank=True,
    )

    def __str__(self):
        return f"Dr. {self.user.get_full_name()}"

class AvailabilitySchedule(models.Model):
    DAY_CHOICES = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name="schedules",
    )
    day_of_week = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        # Prevents overlapping blocks at the DB constraint level
        unique_together = ("doctor", "day_of_week", "start_time")

    def __str__(self):
        return f"Dr. {self.doctor.user.get_full_name()} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"