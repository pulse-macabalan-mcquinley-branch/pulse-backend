import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestUserRegistration:
    url = "/api/v1/auth/users/"

    def test_register_success(self, api_client):
        payload = {
            "email"             : "new@example.com",
            "first_name"        : "Jane",
            "last_name"         : "Doe",
            "password"          : "StrongPass@1",
            "re_password"       : "StrongPass@1",
        }
        response = api_client.post(self.url, payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert "id" in response.data

    def test_register_duplicate_email(self, api_client, user):
        payload = {
            "email"       : user.email,
            "first_name"  : "Dup",
            "last_name"   : "User",
            "password"    : "StrongPass@1",
            "re_password" : "StrongPass@1",
        }
        response = api_client.post(self.url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_weak_password(self, api_client):
        payload = {
            "email"       : "weak@example.com",
            "first_name"  : "Weak",
            "last_name"   : "Pass",
            "password"    : "123",
            "re_password" : "123",
        }
        response = api_client.post(self.url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestJWTAuth:
    login_url = "/api/v1/auth/jwt/create/"

    def test_login_success(self, api_client, user):
        payload = {"email": user.email, "password": "Test@1234"}
        response = api_client.post(self.login_url, payload)
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_wrong_password(self, api_client, user):
        payload = {"email": user.email, "password": "wrong"}
        response = api_client.post(self.login_url, payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestMeEndpoint:
    url = "/api/v1/users/me/"

    def test_get_own_profile(self, auth_client, user):
        response = auth_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email

    def test_update_own_profile(self, auth_client, user):
        response = auth_client.patch(self.url, {"first_name": "Updated"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Updated"

    def test_unauthenticated_rejected(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserListPermissions:
    url = "/api/v1/users/"

    def test_regular_user_cannot_list(self, auth_client):
        response = auth_client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_list(self, admin_client, user):
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data

    def test_admin_can_filter_by_role(self, admin_client, user):
        response = admin_client.get(self.url, {"role": "user"})
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestChangePassword:
    url = "/api/v1/users/me/change-password/"

    def test_change_password_success(self, auth_client):
        payload = {
            "old_password"     : "Test@1234",
            "new_password"     : "NewPass@5678",
            "confirm_password" : "NewPass@5678",
        }
        response = auth_client.post(self.url, payload)
        assert response.status_code == status.HTTP_200_OK

    def test_change_password_wrong_old(self, auth_client):
        payload = {
            "old_password"     : "WrongOld",
            "new_password"     : "NewPass@5678",
            "confirm_password" : "NewPass@5678",
        }
        response = auth_client.post(self.url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST