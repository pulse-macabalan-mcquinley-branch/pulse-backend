from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import UserViewSet

router = DefaultRouter()
router.register(r"", UserViewSet, basename="users")

urlpatterns = [
    path("", include(router.urls)),
]

# Generated endpoints:
#
# GET    /api/v1/users/               → UserViewSet.list     (admin only)
# GET    /api/v1/users/{id}/          → UserViewSet.retrieve
# PATCH  /api/v1/users/{id}/          → UserViewSet.partial_update
# DELETE /api/v1/users/{id}/          → UserViewSet.destroy  (soft delete)
# GET    /api/v1/users/me/            → UserViewSet.me
# PATCH  /api/v1/users/me/            → UserViewSet.me (update profile)
# POST   /api/v1/users/me/change-password/  → UserViewSet.change_password
# PATCH  /api/v1/users/{id}/set-role/ → UserViewSet.set_role (admin only)