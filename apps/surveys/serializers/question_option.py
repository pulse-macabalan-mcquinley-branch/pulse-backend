
from rest_framework import serializers
from ..models import (
    QuestionOption
)

# ── Question Option ───────────────────────────────────────────────────────
class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = [
            'id',
            'question',
            'option_text',
            'option_value',
            'display_order',
            'is_other',
            'image_url',
            'score_weight',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

# ── Question Option: Write (create) ────────────────────────────
class QuestionOptionWriteSerializer(serializers.ModelSerializer):

    option_text = serializers.CharField(
        required=True,
        min_length=1,
        max_length=500,
    )
    option_value = serializers.CharField(
        required=True,
        min_length=1,
        max_length=500,
    )
    class Meta:
        model = QuestionOption
        fields = [
            'id',
            'option_text',
            'option_value',
            'display_order',
            'is_other',
            'image_url',
            'score_weight',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]