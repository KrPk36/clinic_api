import pytest

@pytest.mark.django_db
class TestSpecialtiesPermissions:
    # List action is public
    def test_public_can_list_specialties(self, api_client):
        response = api_client.get("/api/specialties/")

        assert response.status_code == 200

    # Unauthenticated cannot create specialties
    def test_public_cannot_create_specialties(self, api_client):
        response = api_client.post("/api/specialties/", {})

        assert response.status_code == 401
    
    # Patient cannot create specialties
    def test_patient_cannot_create_specialties(self, patient_client):
        response = patient_client.post("/api/specialties/", {})

        assert response.status_code == 403
    
    # Doctor cannot create specialties
    def test_doctor_cannot_create_specialties(self, doctor_client):
        response = doctor_client.post("/api/specialties/", {})

        assert response.status_code == 403
    
    # Admin can create specialties
    def test_admin_can_create_specialties(self, admin_client):
        response = admin_client.post("/api/specialties/", {
            "name":"New specialty",
            "description":"Lorem ipsum...",
        })

        assert response.status_code == 201
        assert "id" in response.data
        assert response.data["name"] == "New specialty"
        assert response.data["description"] == "Lorem ipsum..."

from apps.specialties.models import Specialty
@pytest.mark.django_db
class TestSpecialtyDelete:
    def test_admin_can_delete_unassigned_specialty(self, admin_client):
        specialty = Specialty.objects.create(name="Unassigned")
        response = admin_client.delete(f"/api/specialties/{specialty.pk}/")

        assert response.status_code == 204
        assert not Specialty.objects.filter(pk=specialty.pk).exists()

    def test_cannot_delete_specialty_with_assigned_doctors(self, admin_client, doctor_user):
        specialty = doctor_user.doctor_profile.specialties.first()
        response = admin_client.delete(f"/api/specialties/{specialty.pk}/")
        
        assert response.status_code == 409
        assert Specialty.objects.filter(pk=specialty.pk).exists()