from rest_framework.viewsets import (
    ModelViewSet,
)
from ..serializers import (
    SurveyListSerializer,
    SurveyWriteSerializer,
    SurveyDetailSerializer,
)
from ..models import (
    Survey,
)
from apps.users.models import (
    CustomUser
)
from rest_framework.permissions import (
    IsAuthenticated
)

from drf_spectacular.utils import extend_schema, extend_schema_view
from core.permissions import (
    IsOwner,
    RolePermission
)
from core.pagination import StandardResultsPagination
from django.db.models import Count

@extend_schema_view(
    create=extend_schema(summary="Create a new survey"),
    list=extend_schema(summary="List all surveys"),
    retrieve=extend_schema(summary="Retrieve a survey"),
    update=extend_schema(summary="Update a survey"),
    partial_update=extend_schema(summary="Partially update a survey"),
    destroy=extend_schema(summary="Delete a survey"),
)
class SurveyViewSet(ModelViewSet):
    """
    list, retrieve      → any authenticated user
    create              → RESEARCHER role only
    update, destroy     → owner only
    """

    pagination_class = StandardResultsPagination
    ordering = ["-created_at",]
    required_roles = {
        "create": [CustomUser.Role.RESEARCHER],
    }

    # ── Queryset scoping ──────────────────────────────────────
    def get_queryset(self):
        return Survey.objects.annotate(
            total_questions=Count('questions')
        )

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return SurveyWriteSerializer
        if self.action == 'retrieve':
            return SurveyDetailSerializer
        return SurveyListSerializer
    
    # ── Permissions ───────────────────────────────────────────
    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), RolePermission()]
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsOwner()]
        return [IsAuthenticated()]

    # ── Set created by automatically on create ───────────────────
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)