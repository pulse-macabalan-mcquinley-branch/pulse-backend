import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):
    """Factory fixture for creating users."""
    def _create(email="user@test.com", password="Test@1234", role="user", **kwargs):
        return User.objects.create_user(
            email=email,
            password=password,
            first_name="Test",
            last_name="User",
            role=role,
            **kwargs,
        )
    return _create


@pytest.fixture
def user(create_user):
    return create_user()


@pytest.fixture
def admin_user(create_user):
    return create_user(
        email="admin@test.com", role="admin", is_staff=True
    )


@pytest.fixture
def auth_client(api_client, user):
    """API client authenticated as regular user."""
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """API client authenticated as admin."""
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client