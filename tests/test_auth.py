import pytest, datetime

from apps.common.models import GenderChoices

@pytest.mark.django_db
class TestPatientRegistration:
    # Successful register as a patient
    def test_register_success(self, api_client):
        response = api_client.post(
            "/auth/register/",
            {
                "email":"new@example.com",
                "password":"Test1234!",
                "first_name":"New",
                "last_name":"Patient",
                "date_of_birth":"1999-02-15",
                "phone":"55-9000-100",
                "gender":"F"
            }
        )

        assert response.status_code == 201

        assert "password" not in response.data
        
        assert response.data["email"] == "new@example.com"
        assert response.data["first_name"] == "New"
        assert response.data["last_name"] == "Patient"
        assert response.data["date_joined"] == datetime.date.today().__str__()
        assert response.data["profile"]["date_of_birth"] == "1999-02-15"
        assert response.data["profile"]["gender"] == "Female"
        assert response.data["profile"]["phone"] == "55-9000-100"

    
    # Register fails if email is already in use
    def test_register_duplicate_email(self, api_client, patient_user):
        response = api_client.post(
            "/auth/register/",
            {
                "email":patient_user.email,
                "password":"Test1234!",
                "first_name":"New",
                "last_name":"Patient",
                "date_of_birth":"1999-02-15",
                "phone":"55-9000-100",
                "gender":"F"
            }
        )
        assert response.status_code == 400
    
    # Register fails if receives invalid data
    def test_register_invalid_gender(self, api_client):
        response = api_client.post("/auth/register/", {
            "email": "new@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "Test1234!",
            "date_of_birth": "1995-06-15",
            "phone": "555-9999",
            "gender": "X",  # invalid
        })
        assert response.status_code == 400
