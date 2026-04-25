
from rest_framework import serializers
from ..models import (
    QuestionType,
    Question,
)
from .question_option import (
    QuestionOptionSerializer,
    QuestionOptionWriteSerializer,
)

# ── Question ───────────────────────────────────────────────────────
class QuestionTypeMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionType
        fields = [
            'id',
            'name',
        ]

class QuestionSerializer(serializers.ModelSerializer):
    """ Representation of question """

    type = QuestionTypeMiniSerializer(read_only=True)
    options = QuestionOptionSerializer(many=True, read_only=True)

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
            'options',
            "created_at"
        ]
        read_only_fields = [
            "id",
            'options',
            'type',
            "created_at",
        ]

# ── Question: Write (create) ────────────────────────────
class QuestionWriteSerializer(serializers.ModelSerializer):

    type = serializers.PrimaryKeyRelatedField(
        queryset=QuestionType.objects.all()
    )
    question_text = serializers.CharField(
        required=True,
        min_length=1,
        max_length=500,
    )
    helper_text = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        max_length=500,
    )

    options = QuestionOptionWriteSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = [
            'id',
            'type',
            'question_text',
            'helper_text',
            'display_order',
            'is_required',
            'min_value',
            'max_value',
            'max_length',
            'options',
        ]
        read_only_fields = [
            'id',
        ]

    def validate(self, attrs):
        qtype: QuestionType = attrs.get('type') or getattr(self.instance, 'type', None)
        options = attrs.get('options')

        code = qtype.code.lower()

        min_value = attrs.get('min_value')
        max_value = attrs.get('max_value')
        max_length= attrs.get('max_length')

        CHOICE_TYPES = ['single_choice', 'checkboxes',]
        NUMERIC_TYPES = ['numeric', 'rating', 'scale']

        # ── TEXT ─────────────────────
        if code == 'text':
            if not max_length:
                raise serializers.ValidationError({
                    "max_length": "Required for text questions"
                })

            if min_value is not None or max_value is not None:
                raise serializers.ValidationError(
                    "min_value/max_value not allowed for text type."
                )
            
        # ── NUMBER / RATING / SCALE ─────────────────────
        elif code in NUMERIC_TYPES:
            if min_value is None or max_value is None:
                raise serializers.ValidationError(
                    "min_value and max_value are required."
                )
            if min_value > max_value:
                raise serializers.ValidationError(
                    "min_value cannot be greater than max_value."
                )
            if max_length is not None:
                raise serializers.ValidationError(
                    "max_length not allowed for numeric types."
                )
            
        # ── SINGLE CHOICE / CHECKBOXES ─────────────────────
        elif code in CHOICE_TYPES:
            if not options or len(options) < 2:
                raise serializers.ValidationError({
                    "options": "At least 2 options are required"
                })
            
            values = [opt.get('option_value') for opt in options]
            if len(values) != len(set(values)):
                raise serializers.ValidationError({
                    "options": "option_value must be unique"
                })
            
            if min_value is not None or max_value is not None or max_length is not None:
                raise serializers.ValidationError(
                    "min/max/max_length not allowed for choice types."
                )

        # ── DEFAULT STRICT MODE ──────
        else:
            raise serializers.ValidationError(
                f"Unsupported question type: {code}"
            )
        
        return attrs
