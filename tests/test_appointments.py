import pytest, datetime

@pytest.mark.django_db
class TestAppointmentBooking:

    def test_patient_can_book_appointment(self, patient_client, doctor_user, schedule, future_monday):
        response = patient_client.post("/api/appointments/", {
            "doctor_id": doctor_user.doctor_profile.pk,
            "date": future_monday.isoformat(),
            "start_time": "09:00:00",
        })

        assert response.status_code == 201
        assert response.data["status"] == "scheduled"

    def test_doctor_cannot_book_appointment(self, doctor_client, doctor_user, schedule, future_monday):
        response = doctor_client.post("/api/appointments/", {
            "doctor_id": doctor_user.doctor_profile.pk,
            "date": future_monday.isoformat(),
            "start_time": "09:00:00",
        })

        assert response.status_code == 403

    def test_double_booking_rejected(self, patient_client, appointment, doctor_user, future_monday):
        response = patient_client.post("/api/appointments/", {
            "doctor_id": doctor_user.doctor_profile.pk,
            "date": future_monday.isoformat(),
            "start_time": "09:00:00",  # same slot as fixture appointment
        })

        assert response.status_code == 400

    def test_past_date_rejected(self, patient_client, doctor_user, schedule):
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        response = patient_client.post("/api/appointments/", {
            "doctor_id": doctor_user.doctor_profile.pk,
            "date": yesterday.isoformat(),
            "start_time": "09:00:00",
        })

        assert response.status_code == 400

    def test_invalid_slot_boundary_rejected(self, patient_client, doctor_user, schedule, future_monday):
        response = patient_client.post("/api/appointments/", {
            "doctor_id": doctor_user.doctor_profile.pk,
            "date": future_monday.isoformat(),
            "start_time": "09:15:00",  # not on boundary
        })

        assert response.status_code == 400

    def test_outside_schedule_rejected(self, patient_client, doctor_user, schedule, future_monday):
        response = patient_client.post("/api/appointments/", {
            "doctor_id": doctor_user.doctor_profile.pk,
            "date": future_monday.isoformat(),
            "start_time": "14:00:00",  # outside 09:00-13:00
        })

        assert response.status_code == 400


@pytest.mark.django_db
class TestAppointmentActions:

    def test_patient_can_cancel_own_appointment(self, patient_client, appointment):
        response = patient_client.patch(
            f"/api/appointments/{appointment.pk}/cancel/"
        )

        assert response.status_code == 200
        assert response.data["status"] == "cancelled"

    def test_patient_cannot_cancel_other_patients_appointment(self, api_client, appointment):
        from django.contrib.auth.models import Group
        from apps.user.models import User, PatientProfile

        other_user = User.objects.create_user(
            email="other@example.com",
            password="Patient1234!",
            first_name="Other",
            last_name="Patient",
        )
        other_user.groups.add(Group.objects.get(name="Patient"))
        PatientProfile.objects.create(
            user=other_user,
            date_of_birth="1990-01-01",
            phone="555-8888",
            gender="F",
        )
        api_client.force_authenticate(user=other_user)
        response = api_client.patch(f"/api/appointments/{appointment.pk}/cancel/")

        assert response.status_code == 404

    def test_doctor_can_complete_own_appointment(self, doctor_client, doctor_user, patient_user, schedule):
        # Create a past appointment to complete
        from apps.appointments.models import Appointment
        past_date = datetime.date.today() - datetime.timedelta(days=1)
        past_appointment = Appointment.objects.create(
            doctor=doctor_user.doctor_profile,
            patient=patient_user.patient_profile,
            date=past_date,
            start_time="09:00",
            end_time="09:30",
            status=Appointment.Status.SCHEDULED,
        )
        response = doctor_client.patch(
            f"/api/appointments/{past_appointment.pk}/complete/"
        )

        assert response.status_code == 200
        assert response.data["status"] == "completed"
    
    def test_doctor_cannot_complete_other_doctors_appointment(self, api_client, appointment):
        from django.contrib.auth.models import Group
        from apps.user.models import User
        from apps.doctors.models import DoctorProfile

        appointment.date = datetime.date.today() - datetime.timedelta(days=1)
        appointment.save()

        other_user = User.objects.create_user(
            email="other_doctor@example.com",
            password="Doctor1234!",
            first_name="Other",
            last_name="Doctor",
        )
        other_user.groups.add(Group.objects.get(name="Doctor"))
        DoctorProfile.objects.create(
            user=other_user,
            phone="500-101",
        )
        api_client.force_authenticate(user=other_user)
        response = api_client.patch(f"/api/appointments/{appointment.pk}/complete/")

        assert response.status_code == 404

    def test_patient_cannot_complete_appointment(self, patient_client, appointment):
        response = patient_client.patch(
            f"/api/appointments/{appointment.pk}/complete/"
        )

        assert response.status_code == 403

    def test_cannot_cancel_already_cancelled_appointment(self, patient_client, appointment):
        patient_client.patch(f"/api/appointments/{appointment.pk}/cancel/")
        response = patient_client.patch(f"/api/appointments/{appointment.pk}/cancel/")

        assert response.status_code == 400