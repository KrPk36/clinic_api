from django.contrib.auth.models import Group
from rest_framework.test import APIClient
import pytest, datetime

from apps.user.models import User, PatientProfile
from apps.doctors.models import DoctorProfile, AvailabilitySchedule
from apps.specialties.models import Specialty
from apps.appointments.models import Appointment, SLOT_DURATION_MINUTES

@pytest.fixture(autouse=True)
def create_groups(db):
    for name in ["Admin","Doctor","Patient"]:
        Group.objects.get_or_create(name=name)

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture()
def admin_user(db):
    user = User.objects.create_superuser(
        email="admin@clinic.com",
        password="Admin1234!",
        first_name="Admin",
        last_name="User",
    )
    return user

@pytest.fixture
def doctor_user(db):
    user:User= User.objects.create_user(
        email="dr.test@clinic.com",
        password="Doctor1234!",
        first_name="Test",
        last_name="Doctor",
    )
    user.groups.add(Group.objects.get(name="Doctor"))
    specialty = Specialty.objects.create(name="General Practice")
    profile = DoctorProfile.objects.create(user=user, phone="500-001")
    profile.specialties.set([specialty])
    return user

@pytest.fixture
def patient_user(db):
    user:User = User.objects.create(
        email="patient@example.com",
        password="Patient1234!",
        first_name="Test",
        last_name="Patient",
    )
    user.groups.add(Group.objects.get(name="Patient"))
    PatientProfile.objects.create(
        user=user,
        date_of_birth="1990-01-01",
        phone="500-0002",
        gender="M",
    )
    return user

@pytest.fixture
def schedule(db, doctor_user):
    return AvailabilitySchedule.objects.create(
        doctor=doctor_user.doctor_profile,
        day_of_week=0,
        start_time="09:00",
        end_time="13:00",
    )

@pytest.fixture
def future_monday(db):
    today = datetime.date.today()
    days_ahead = 0 - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + datetime.timedelta(days=days_ahead)

@pytest.fixture
def appointment(db, doctor_user, patient_user, schedule, future_monday):
    return Appointment.objects.create(
        doctor=doctor_user.doctor_profile,
        patient=patient_user.patient_profile,
        date=future_monday,
        start_time="09:00",
        end_time="09:30",
        status=Appointment.Status.SCHEDULED,
    )

# Authentication helpers
@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def doctor_client(api_client, doctor_user):
    api_client.force_authenticate(user=doctor_user)
    return api_client


@pytest.fixture
def patient_client(api_client, patient_user):
    api_client.force_authenticate(user=patient_user)
    return api_client