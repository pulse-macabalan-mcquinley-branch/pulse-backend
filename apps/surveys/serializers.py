from rest_framework import serializers
from .models import (
    QuestionType,
    DeviceType,
    Survey,
    Question,
    Response,
    Answer,
)
from ..users.serializers import UserSerializer

# ── Question Type ───────────────────────────────────────────────────────
class QuestionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionType
        fields = [
            "id",
            "code",
            "name"
        ]
        read_only_fields = [
            "id"
        ]

# ── Device Type ───────────────────────────────────────────────────────
class DeviceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceType
        fields = [
            "id",
            "code",
            "name"
        ]
        read_only_fields = [
            "id"
        ]

# ── Question ───────────────────────────────────────────────────────
class QuestionSerializer(serializers.ModelSerializer):
    """ Representation of question """

    type = QuestionTypeSerializer(read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "type",
            "question_text",
            "helper_text",
            "display_order",
            "is_required",
            "min_value",
            "max_value",
            "max_length",
            "image_url",
            "created_at"
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]

# ── Answer ───────────────────────────────────────────────────────
class AnswerSerializer(serializers.ModelSerializer):
    """ Representation of answer """

    question = QuestionSerializer(read_only=True)

    class Meta:
        model = Answer
        fields = [
            "id",
            "question",
            "answer_text",
            "answer_number",
            "answer_date",
            "answer_json",
            "file_url",
            "was_skipped",
            "created_at",
        ]

# ── Response ───────────────────────────────────────────────────────
class ResponseSerializer(serializers.ModelSerializer):
    """ Representation of response """

    submitted_by = UserSerializer(read_only=True)
    device_type = DeviceTypeSerializer(read_only=True)

    class Meta:
        model = Response
        fields = [
            "id",
            "submitted_by",
            "device_type",
            "status",
            "duration_seconds",
            "is_flagged",
            "flag_reason",
            "is_offline_submitted",
            "synced_at",
            "submitted_at",
            "created_at",
        ]


# ── Survey: List (lightweight) ───────────────────────────────────────────────────────
class SurveyListSerializer(serializers.ModelSerializer):
    """Lean representation for survey endpoints — no full body."""

    class Meta:
        model = Survey
        fields = [
            "id",
            "title",
            "description",
            "status",
            "published_at",
            "closes_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]

# ── Survey: Detail (full body) ───────────────────────────────────────────────────────
class SurveyDetailSerializer(SurveyListSerializer):
    """Full survey including other attributes — used on retrieve."""
    
    created_by = UserSerializer(read_only=True)
    questions = QuestionSerializer(many=True, read_only=True)
    responses = ResponseSerializer(many=True, read_only=True)

    class Meta(SurveyListSerializer.Meta):
        fields = SurveyListSerializer.Meta.fields + [
            "created_by",
            "offline_enabled",
            "allow_anonymous",
            "response_limit",
            "show_progress_bar",
            "one_response_per_user",
            "published_at",
            "closes_at",
            "questions",
            "responses",
        ]
        read_only_fields = SurveyListSerializer.Meta.read_only_fields + [
            "created_by",
        ]