from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import DoctorViewSet, AvailabilityScheduleViewSet

router = DefaultRouter()
router.register(r"doctors", DoctorViewSet, basename="doctor")

urlpatterns = router.urls + [
    path(
        "doctors/<int:doctor_pk>/schedules/",
        AvailabilityScheduleViewSet.as_view({
            "get": "list",
            "post": "create",
        }),
        name="doctor-schedule-list",
    ),
    path(
        "doctors/<int:doctor_pk>/schedules/<int:pk>/",
        AvailabilityScheduleViewSet.as_view({
            "get": "retrieve",
            "put": "update",
            "patch": "partial_update",
            "delete": "destroy",
        }),
        name="doctor-schedules-detail",
    ),
]