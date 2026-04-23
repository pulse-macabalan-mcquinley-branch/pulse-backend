from rest_framework.viewsets import (
    ReadOnlyModelViewSet,
    ModelViewSet,
)
from .serializers import (
    DeviceTypeSerializer,
    QuestionTypeSerializer,
    SurveyListSerializer,
    SurveyWriteSerializer,
)
from .models import (
    DeviceType,
    QuestionType,
    Survey,
)
from apps.users.models import (
    CustomUser
)
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated
)
from core.throttling import (
    AnonBurstThrottle,
    AnonSustainedThrottle
)
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from core.permissions import (
    IsResearcher,
    IsOwner,
    RolePermission
)
from django.db.models import Q
from core.pagination import StandardResultsPagination

class DeviceTypeViewSet(ReadOnlyModelViewSet):
    """
    Read-only device type list/detail. No auth required.
    """

    queryset = DeviceType.objects.all()
    serializer_class = DeviceTypeSerializer
    permission_classes = [AllowAny]
    ordering = ["code", "name"]
    pagination_class = None

    throttle_classes = [
        AnonBurstThrottle,
        AnonSustainedThrottle,
    ]

class QuestionTypeViewSet(ReadOnlyModelViewSet):
    """
    Read-only question type list/detail. No auth required.
    """

    queryset = QuestionType.objects.all()
    serializer_class = QuestionTypeSerializer
    permission_classes = [AllowAny]
    ordering = ["code", "name"]
    pagination_class = None
    
    throttle_classes = [
        AnonBurstThrottle,
        AnonSustainedThrottle,
    ]

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
        return Survey.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return SurveyListSerializer
        return SurveyWriteSerializer
    
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