from django.contrib import admin

from .models import DoctorProfile, AvailabilitySchedule

# Register your models here.
admin.site.register(DoctorProfile)
admin.site.register(AvailabilitySchedule)