from rest_framework import serializers
from ..models import (
    Answer,
    Response,
)
from .question import (
    QuestionSerializer,
)
from ...users.serializers import (
    UserSerializer
)
from .base import (
    DeviceTypeSerializer
)

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


