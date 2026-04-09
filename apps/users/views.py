from django.contrib.auth import update_session_auth_hash
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import (
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from core.exceptions import ResourceNotFound
from core.pagination import StandardResultsPagination
from core.permissions import IsOwnerOrAdmin, RolePermission
from core.throttling import SensitiveEndpointThrottle

from .models import CustomUser
from .serializers import (
    AdminUserRoleSerializer,
    ChangePasswordSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


class UserViewSet(
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    """
    /api/v1/users/
    GET     → list users (admin only)
    GET  id → retrieve user
    PATCH   → update own profile or admin updates any
    DELETE  → deactivate (soft delete via is_active=False)
    """

    queryset           = CustomUser.objects.active().order_by("-date_joined")
    serializer_class   = UserSerializer
    pagination_class   = StandardResultsPagination
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    search_fields      = ["email", "first_name", "last_name"]
    ordering_fields    = ["date_joined", "email"]
    filterset_fields   = ["role", "is_active"]

    required_roles = {
        "list":    ["admin", "superadmin"],
        "destroy": ["admin", "superadmin"],
    }

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return UserUpdateSerializer
        if self.action == "set_role":
            return AdminUserRoleSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == "list":
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()

    def perform_destroy(self, instance):
        """Soft delete — deactivate instead of removing from DB."""
        instance.is_active = False
        instance.save(update_fields=["is_active"])

    # ── /users/me/ ────────────────────────────────────────────
    @extend_schema(responses=UserSerializer)
    @action(detail=False, methods=["get", "patch"], url_path="me",
            permission_classes=[IsAuthenticated])
    def me(self, request):
        if request.method == "PATCH":
            serializer = UserUpdateSerializer(
                request.user, data=request.data, partial=True,
                context={"request": request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(UserSerializer(request.user).data)

        return Response(UserSerializer(request.user).data)

    # ── /users/me/change-password/ ────────────────────────────
    @extend_schema(request=ChangePasswordSerializer, responses={200: None})
    @action(detail=False, methods=["post"], url_path="me/change-password",
            permission_classes=[IsAuthenticated],
            throttle_classes=[SensitiveEndpointThrottle])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Keep session active after password change
        update_session_auth_hash(request, user)
        return Response(
            {"detail": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )

    # ── /users/{id}/set-role/ (admin only) ───────────────────
    @extend_schema(request=AdminUserRoleSerializer, responses=UserSerializer)
    @action(detail=True, methods=["patch"], url_path="set-role",
            permission_classes=[IsAuthenticated, IsAdminUser])
    def set_role(self, request, pk=None):
        user = self.get_object()
        serializer = AdminUserRoleSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(user).data)