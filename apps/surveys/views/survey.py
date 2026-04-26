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
    IsAuthenticated,
    AllowAny
)

from drf_spectacular.utils import extend_schema, extend_schema_view
from core.permissions import (
    IsOwner,
    RolePermission
)
from core.pagination import StandardResultsPagination
from django.db.models import Count
from rest_framework.response import Response
from rest_framework.decorators import action

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
        if self.action == "published":
            return [AllowAny()]
        if self.action == "create":
            return [IsAuthenticated(), RolePermission()]
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsOwner()]
        return [IsAuthenticated()]

    # ── Set created by automatically on create ───────────────────
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    # ── Published surveys (public) ────────────────────────────
    @extend_schema(summary="List published surveys - auth depends on allow_anonymous")
    @action(detail=False, methods=["get"], url_path="published")
    def published(self, request):
        qs = Survey.objects.filter(
            published_at__isnull=False
        ).annotate(
            total_questions=Count("questions")
        ).select_related("created_by").order_by("-published_at")

        # ── Unauthenticated → only show allow_anonymous surveys ──
        if not request.user.is_authenticated:
            qs = qs.filter(allow_anonymous=True)
        
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = SurveyListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = SurveyListSerializer(qs, many=True)
        return Response(serializer.data)