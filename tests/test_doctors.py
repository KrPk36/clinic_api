from django.contrib.auth.models import Group
import pytest

from apps.appointments.models import Appointment
from apps.doctors.models import DoctorProfile, AvailabilitySchedule
from apps.specialties.models import Specialty
from apps.user.models import User

@pytest.mark.django_db
class TestDoctorPermissions:

    def test_public_can_list_doctors(self, api_client):
        response = api_client.get("/api/doctors/")

        assert response.status_code == 200

    def test_public_can_retrieve_doctor(self, api_client, doctor_user):
        response = api_client.get(f"/api/doctors/{doctor_user.doctor_profile.pk}/")

        assert response.status_code == 200

    def test_patient_cannot_create_doctor(self, patient_client):
        response = patient_client.post("/api/doctors/", {})

        assert response.status_code == 403
    
    def test_doctor_cannot_create_doctor(self, doctor_client):
        response = doctor_client.post("/api/doctors/", {})

        assert response.status_code == 403

    def test_unauthenticated_cannot_create_doctor(self, api_client):
        response = api_client.post("/api/doctors/", {})

        assert response.status_code == 401

@pytest.mark.django_db
class TestDoctorFilters:

    def test_filter_by_specialty(self, api_client, doctor_user):
        specialty = doctor_user.doctor_profile.specialties.first()
        response = api_client.get(
            f"/api/doctors/?specialty_id={specialty.pk}"
        )

        assert response.status_code == 200
        assert all(
            any(
                specialty_["id"] == specialty.pk for specialty_ in doctor["specialties"]
            ) for doctor in response.data
        )

    def test_filter_by_nonexistent_specialty_returns_empty(self, api_client):
        response = api_client.get("/api/doctors/?specialty_id=99999")
        assert response.status_code == 200
        assert len(response.data) == 0

@pytest.mark.django_db
class TestDoctorSoftDelete:

    def test_delete_deactivates_instead_of_removing(self, admin_client, doctor_user):
        response = admin_client.delete(f"/api/doctors/{doctor_user.doctor_profile.pk}/")
        
        assert response.status_code == 204

        doctor_user.doctor_profile.refresh_from_db()

        assert doctor_user.doctor_profile.is_active is False

    def test_deactivated_doctor_excluded_from_list(self, api_client, doctor_user):
        doctor_user.doctor_profile.is_active = False
        doctor_user.doctor_profile.save()
        response = api_client.get("/api/doctors/")
        ids = [d["id"] for d in response.data]

        assert doctor_user.doctor_profile.pk not in ids

@pytest.mark.django_db
class TestDoctorCreation:

    def test_admin_can_create_doctor(self, admin_client):
        specialty = Specialty.objects.create(name="Cardiology")
        response = admin_client.post("/api/doctors/", {
            "email": "new.doctor@clinic.com",
            "password": "Doctor1234!",
            "first_name": "New",
            "last_name": "Doctor",
            "phone": "555-1234",
            "specialty_ids": [specialty.pk],
        })

        assert response.status_code == 201
        assert "id" in response.data
        assert response.data["name"] == "New Doctor"
        assert response.data["phone"] == "555-1234"
        assert len(response.data["specialties"]) == 1

    def test_created_doctor_assigned_to_doctor_group(self, admin_client):
        specialty = Specialty.objects.create(name="Cardiology")
        response = admin_client.post("/api/doctors/", {
            "email": "new.doctor@clinic.com",
            "password": "Doctor1234!",
            "first_name": "New",
            "last_name": "Doctor",
            "phone": "555-1234",
            "specialty_ids": [specialty.pk],
        })
        user = User.objects.get(email="new.doctor@clinic.com")

        assert user.groups.filter(name="Doctor").exists()

    def test_duplicate_email_rejected(self, admin_client, doctor_user):
        specialty = Specialty.objects.create(name="Cardiology")
        response = admin_client.post("/api/doctors/", {
            "email": doctor_user.email,
            "password": "Doctor1234!",
            "first_name": "Dupe",
            "last_name": "Doctor",
            "phone": "555-0000",
            "specialty_ids": [specialty.pk],
        })

        assert response.status_code == 400

@pytest.mark.django_db
class TestSchedulePermissions:

    def test_public_can_list_schedules(self, api_client, doctor_user):
        response = api_client.get(
            f"/api/doctors/{doctor_user.doctor_profile.pk}/schedules/"
        )

        assert response.status_code == 200

    def test_doctor_cannot_add_schedule_to_other_doctor(self, doctor_client):
        other_user = User.objects.create_user(
            email="other@clinic.com",
            password="Doctor1234!",
            first_name="Other",
            last_name="Doctor",
        )
        other_user.groups.add(Group.objects.get(name="Doctor"))
        other_profile = DoctorProfile.objects.create(
            user=other_user, phone="555-9999"
        )
        response = doctor_client.post(
            f"/api/doctors/{other_profile.pk}/schedules/",
            {"day_of_week": 1, "start_time": "09:00", "end_time": "13:00"},
        )

        assert response.status_code == 403

    def test_doctor_cannot_update_other_doctors_schedule(self, doctor_client):
        other_user = User.objects.create_user(
            email="other@clinic.com",
            password="Doctor1234!",
            first_name="Other",
            last_name="Doctor",
        )
        other_user.groups.add(Group.objects.get(name="Doctor"))
        other_profile = DoctorProfile.objects.create(
            user=other_user, phone="555-9999"
        )
        other_schedule = AvailabilitySchedule.objects.create(
            doctor=other_profile,
            day_of_week=1,
            start_time="09:00",
            end_time="13:00",
        )
        response = doctor_client.patch(
            f"/api/doctors/{other_profile.pk}/schedules/{other_schedule.pk}/",
            {"start_time": "10:00"},
        )

        assert response.status_code == 403

@pytest.mark.django_db
class TestScheduleValidation:
    # Already existing schedule is Mon 09:00-13:00,

    def test_overlapping_block_rejected(self, doctor_client, doctor_user, schedule):
        response = doctor_client.post(
            f"/api/doctors/{doctor_user.doctor_profile.pk}/schedules/",
            {
                "day_of_week": 0, 
                "start_time": "10:00",
                "end_time": "14:00"
            },
        )

        assert response.status_code == 400

    def test_non_overlapping_same_day_accepted(self, doctor_client, doctor_user, schedule):
        response = doctor_client.post(
            f"/api/doctors/{doctor_user.doctor_profile.pk}/schedules/",
            {"day_of_week": 0, "start_time": "14:00", "end_time": "18:00"},
        )

        assert response.status_code == 201

    def test_end_time_before_start_time_rejected(self, doctor_client, doctor_user):
        response = doctor_client.post(
            f"/api/doctors/{doctor_user.doctor_profile.pk}/schedules/",
            {"day_of_week": 1, "start_time": "13:00", "end_time": "09:00"},
        )

        assert response.status_code == 400

@pytest.mark.django_db
class TestAvailableSlots:
    # schedule fixture goes form 9:00 - 13:00

    def test_returns_all_slots_when_no_appointments(self, api_client, doctor_user, schedule, future_monday):
        response = api_client.get(
            f'/api/doctors/{doctor_user.doctor_profile.pk}/available_slots/?date={future_monday.isoformat()}'
        )

        assert response.status_code == 200
        assert response.data["available_slots"] == [
            "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30"
        ]
    
    # appointment fixture booked at 09:00
    def test_booked_slot_not_in_list(self, api_client, doctor_user, schedule, appointment, future_monday):
        response = api_client.get(
            f'/api/doctors/{doctor_user.doctor_profile.pk}/available_slots/?date={future_monday.isoformat()}'
        )

        assert response.status_code == 200
        assert response.data["available_slots"] == [
            "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30"
        ]
    
    def test_slot_not_listed_after_booking_appointment(self, api_client, patient_user, doctor_user, schedule, future_monday):
        Appointment.objects.create(
            patient=patient_user.patient_profile,
            doctor=doctor_user.doctor_profile,
            date=future_monday,
            start_time="10:00",
            end_time="10:30",
            status=Appointment.Status.SCHEDULED
        )
        response = api_client.get(
            f'/api/doctors/{doctor_user.doctor_profile.pk}/available_slots/?date={future_monday.isoformat()}'
        )
        assert response.status_code == 200
        assert response.data["available_slots"] == [
            "09:00", "09:30", "10:30", "11:00", "11:30", "12:00", "12:30"
        ]
    
    def test_cancelled_appointment_does_not_block_slot(self, api_client, patient_user, doctor_user, schedule, future_monday):
        Appointment.objects.create(
            patient=patient_user.patient_profile,
            doctor=doctor_user.doctor_profile,
            date=future_monday,
            start_time="10:00",
            end_time="10:30",
            status=Appointment.Status.CANCELLED
        )
        response = api_client.get(
            f'/api/doctors/{doctor_user.doctor_profile.pk}/available_slots/?date={future_monday.isoformat()}'
        )
        assert response.status_code == 200
        assert response.data["available_slots"] == [
            "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30"
        ]

    def test_no_schedule_on_requested_day_returns_empty(self, api_client, doctor_user, schedule):
        # schedule fixture is Monday, so Sunday should have nothing
        from datetime import date, timedelta

        today = date.today()
        days_ahead = (6 - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7  # not today, always a future date
        next_sunday = today + timedelta(days=days_ahead)
        response = api_client.get(
            f"/api/doctors/{doctor_user.doctor_profile.pk}/available_slots/?date={next_sunday.isoformat()}"
        )

        assert response.status_code == 200
        assert response.data["available_slots"] == []

    def test_missing_date_param_returns_400(self, api_client, doctor_user):
        response = api_client.get(
            f"/api/doctors/{doctor_user.doctor_profile.pk}/available_slots/",
        )

        assert response.status_code == 400