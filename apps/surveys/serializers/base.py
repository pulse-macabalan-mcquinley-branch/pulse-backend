from rest_framework import serializers
from ..models import (
    QuestionType,
    DeviceType,
)

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