import pytest, datetime

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

@pytest.mark.django_db
class TestLogin:
    # Successful login
    def test_login_success(self, api_client, patient_user):
        response = api_client.post("/auth/login/", {
            "email":patient_user.email,
            "password":"Patient1234!",
        })
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data
    
    # Login attempt with wrong credentials
    def test_login_wrong_password(self, api_client, patient_user):
        response = api_client.post("/auth/login/", {
            "email":patient_user.email,
            "password":"WrongPassword",
        })
        assert response.status_code == 400

@pytest.mark.django_db
class TestTokenRefresh:
    # Get a new access token using a valid refresh token
    def test_refresh_success(self, api_client, patient_user):
        # Get valid pair token first
        login_response = api_client.post("/auth/login/", {
            "email":patient_user.email,
            "password":"Patient1234!",
        })

        refresh_token = login_response.data["refresh"]

        response = api_client.post("/auth/token/refresh/",{
            "refresh":refresh_token
        })

        assert response.status_code == 200
        assert "access" in response.data
    
    # Refresh fails when receiving an invalid refresh token
    def test_refresh_with_invalid_token(self, api_client):
        response = api_client.post("/auth/token/refresh/", {
            "refresh":"this-is-an-invalid-token"
        })

        assert response.status_code == 401

@pytest.mark.django_db
class TestMe:
    # Get own profile as Patient
    def test_get_patient_profile(self, patient_client, patient_user):
        response = patient_client.get("/auth/me/")

        assert response.status_code == 200
        assert response.data["email"] == patient_user.email
        assert response.data["first_name"] == patient_user.first_name
        assert response.data["last_name"] == patient_user.last_name
        assert "date_of_birth" in response.data["profile"]
    
    # Get own profile as Doctor
    def test_get_doctor_profile(self, doctor_client, doctor_user):
        response = doctor_client.get("/auth/me/")

        assert response.status_code == 200
        assert response.data["email"] == doctor_user.email
        assert response.data["first_name"] == doctor_user.first_name
        assert response.data["last_name"] == doctor_user.last_name
        assert "bio" in response.data["profile"]
        assert "specialties" in response.data["profile"]
    
    # Try to get profile while unaunthenticated
    def test_get_profile_unauthenticated(self, api_client):
        response = api_client.get("/auth/me/")

        assert response.status_code == 401
    
    # Patch own data
    def test_patch_own_name(self, patient_client, patient_user):
        response = patient_client.patch("/auth/me/", {
            "first_name": "Updated",
        })

        assert response.status_code == 200
        assert response.data["first_name"] == "Updated"
        patient_user.refresh_from_db()
        assert patient_user.first_name == "Updated"
    
    # Change own password
    def test_patch_password(self, patient_client, patient_user):
        response = patient_client.patch("/auth/me/", {
            "password": "NewPassword1234!",
        })

        assert response.status_code == 200
        patient_user.refresh_from_db()
        assert patient_user.check_password("NewPassword1234!")
    
    # Patch doesn't allow email change
    def test_cannot_change_email(self, patient_client, patient_user):
        original_email = patient_user.email
        response = patient_client.patch("/auth/me/", {
            "email": "newemail@example.com",
        })
        patient_user.refresh_from_db()
        
        # Email must remain unchanged regardless of response status
        assert patient_user.email == original_email