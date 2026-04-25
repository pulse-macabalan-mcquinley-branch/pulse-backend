from rest_framework import serializers
from .models import (
    QuestionType,
    DeviceType,
    Survey,
    Question,
    Response,
    Answer,
    QuestionOption,
)
from ..users.serializers import UserSerializer
from django.utils import timezone

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

# ── Survey: List (lightweight) ──────────────────────────────────
class SurveyListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for list views.
    Omits heavy fields like description — fetch those on retrieve.
    """
    created_by = serializers.StringRelatedField(read_only=True)
    total_questions = serializers.IntegerField(read_only=True)

    class Meta:
        model = Survey
        fields = [
            'id',
            'title',
            'status',
            'created_by',
            'offline_enabled',
            'allow_anonymous',
            'response_limit',
            'total_questions',
            'closes_at',
            'created_at',
        ]
        read_only_fields = fields

# ── Question Option: Write (create) ────────────────────────────
class QuestionOptionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = [
            'option_text',
            'option_value',
            'display_order',
            'is_other',
            'image_url',
            'score_weight',
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

# ── Survey: Write (create) ────────────────────────────
class SurveyWriteSerializer(serializers.ModelSerializer):
    """
    Handles create / partial-update payloads for Survey.
    Status transitions are intentionally excluded — use SurveyStatusSerializer.
    """
    title = serializers.CharField(
        max_length=255,
        required=True,
        trim_whitespace=True,
    )
    description = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        max_length=1000
    )
    response_limit = serializers.IntegerField(
        min_value=1,
        allow_null=True,
        required=False
    )
    closes_at = serializers.DateTimeField(
        required=False,
        allow_null=True
    )

    questions = QuestionWriteSerializer(many=True, required=False)

    class Meta:
        model = Survey
        fields = [
            'id',
            'title',
            'description',
            'status',
            'offline_enabled',
            'allow_anonymous',
            'one_response_per_user',
            'response_limit',
            'closes_at',
            'questions',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'created_at',
            'updated_at',
        ]

    # ── Field-level validation ────────────────────────
    def validate_closes_at(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError("Close date must be in the future.")
        return value
    
    # ── Object-level validation ───────────────────────
    def validate(self, attrs: dict) -> dict:
        # Merge with existing instance values on PATCH so partial updates
        # don't bypass cross-field rules.
        anonymous    = attrs.get("allow_anonymous",      getattr(self.instance, "allow_anonymous",      False))
        one_per_user = attrs.get("one_response_per_user", getattr(self.instance, "one_response_per_user", False))

        if anonymous and one_per_user:
            raise serializers.ValidationError(
                "allow_anonymous and one_response_per_user are mutually exclusive."
            )

        return attrs
    
    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        survey = Survey.objects.create(**validated_data)

        question_instances = []
        options_to_create = []

        # First pass: create question instances (without saving yet)
        for q in questions_data:
            options = q.pop('options', [])
            question = Question(survey=survey, **q)
            question_instances.append((question, options))
        
        # Bulk create questions
        created_questions = Question.objects.bulk_create(
            [q for q, _ in question_instances]
        )

        # Second pass: attach options
        for question, (_,options) in zip(created_questions, question_instances):
            for opt in options:
                options_to_create.append(
                    QuestionOption(question=question, **opt)
                )
        
        # Bulk create options
        if options_to_create:
            QuestionOption.objects.bulk_create(options_to_create)

        return survey
    
