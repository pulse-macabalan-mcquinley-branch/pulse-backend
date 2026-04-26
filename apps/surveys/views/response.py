from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response as DRFResponse
from drf_spectacular.utils import extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from ..models import Response, Survey
from ..serializers import ResponseSerializer, ResponseSubmitSerializer
from core.permissions import IsSurveyOwner
from django.shortcuts import get_object_or_404
from ..filters import (
    ResponseFilter
)

@extend_schema_view(
    list=extend_schema(summary="List responses for a survey"),
    retrieve=extend_schema(summary="Retrieve a response"),
    destroy=extend_schema(summary="Delete a response"),
)
class ResponseViewSet(ModelViewSet):
    """
    Nested under /surveys/{survey_pk}/responses/

    list, retrieve  → survey owner only
    destroy         → survey owner only
    submit          → AllowAny, filtered by allow_anonymous
    """
    http_method_names = ["get", "delete", "post", "head", "options"]
    filter_backends   = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class   = ResponseFilter
    search_fields     = ["submitted_by__email", "submitted_by__full_name", "flag_reason"]
    ordering_fields   = ["submitted_at", "duration_seconds", "status", "is_flagged"]
    ordering          = ["-submitted_at"]

    def get_survey(self):
        return get_object_or_404(Survey, pk=self.kwargs["survey_pk"])

    def get_queryset(self):
        return Response.objects.filter(
            survey_id=self.kwargs["survey_pk"]
        ).select_related(
            "submitted_by",
            "device_type",
        ).prefetch_related(
            "answers__question",
        ).order_by("-submitted_at")

    def get_serializer_class(self):
        if self.action == "submit":
            return ResponseSubmitSerializer
        return ResponseSerializer

    def get_permissions(self):
        if self.action == "submit":
            return [AllowAny()]
        return [IsAuthenticated(), IsSurveyOwner()]

    # ── Submit a response ─────────────────────────────────────
    @extend_schema(summary="Submit answers to a survey")
    @action(detail=False, methods=["post"], url_path="submit")
    def submit(self, request, survey_pk=None):
        survey = self.get_survey()

        # ── Survey must be published ──────────────────────────
        if survey.status != Survey.Status.PUBLISHED:
            return DRFResponse(
                {"detail": "This survey is not accepting responses."},
                status=400
            )

        # ── Anonymous check ───────────────────────────────────
        if not survey.allow_anonymous and not request.user.is_authenticated:
            return DRFResponse(
                {"detail": "Authentication required to respond to this survey."},
                status=401
            )

        serializer = ResponseSubmitSerializer(
            data=request.data,
            context={"survey": survey, "request": request}
        )
        serializer.is_valid(raise_exception=True)
        response = serializer.save()

        return DRFResponse(
            ResponseSerializer(response).data,
            status=201
        )