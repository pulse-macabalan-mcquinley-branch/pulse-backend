
from rest_framework.viewsets import (
    ModelViewSet,
)
from ...users.models import (
    CustomUser
)
from ..models import (
    Question,
    Survey,
)
from ..serializers import (
    QuestionWriteSerializer,
    QuestionSerializer,
)
from rest_framework.permissions import (
    IsAuthenticated
)
from core.permissions import (
    RolePermission,
    IsOwner,
)
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema_view(
    create=extend_schema(summary="Add a question to a survey"),
    list=extend_schema(summary="List all questions in a survey"),
    retrieve=extend_schema(summary="Retrieve a question"),
    update=extend_schema(summary="Update a question"),
    partial_update=extend_schema(summary="Partially update a question"),
    destroy=extend_schema(summary="Delete a question"),
)
class QuestionViewSet(ModelViewSet):
    """
    Nested under /surveys/{survey_pk}/questions
    
    list, retrieve  → any authenticated user
    create, update,
    partial_update,
    destroy         → Researcher + owns the parent survey  
    """
    pagination_class = None
    required_roles = {
        "create":         [CustomUser.Role.RESEARCHER],
        "update":         [CustomUser.Role.RESEARCHER],
        "partial_update": [CustomUser.Role.RESEARCHER],
        "destroy":        [CustomUser.Role.RESEARCHER],
    }

    def get_queryset(self):
        return Question.objects.filter(
            survey_id=self.kwargs["survey_pk"]
        ).select_related("type").prefetch_related("options").order_by("display_order")
    
    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return QuestionWriteSerializer
        return QuestionSerializer
    
    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), RolePermission(), IsOwner()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        serializer.save(survey=get_object_or_404(Survey, pk=self.kwargs['survey_pk']))