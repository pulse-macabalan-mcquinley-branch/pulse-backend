from rest_framework import serializers
from ..models import (
    Survey,
    Question,
    QuestionOption,
)
from .question import (
    QuestionSerializer,
    QuestionWriteSerializer,
)
from .response import (
    ResponseSerializer
)
from django.utils import timezone

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


# ── Survey: Detail (full body) ───────────────────────────────────────────────────────
class SurveyDetailSerializer(SurveyListSerializer):
    """Full survey including other attributes — used on retrieve."""
    
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
            'created_by'
        ]

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
        for question, (_, options) in zip(created_questions, question_instances):
            for opt in options:
                options_to_create.append(
                    QuestionOption(question=question, **opt)
                )
        
        # Bulk create options
        if options_to_create:
            QuestionOption.objects.bulk_create(options_to_create)

        return survey
    
    def update(self, instance, validated_data):
        questions_data = validated_data.pop("questions", None)

        # ── Update flat survey fields ─────────────────────────
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()

        # ── If questions not provided on PATCH, leave them alone
        if questions_data is None:
            return instance
        
        # ── Replace all questions on PUT/PATCH with questions ─
        existing_ids = [q.get("id") for q in questions_data if q.get("id")]

        # Delete questions not in the new payload
        instance.questions.exclude(id__in=existing_ids).delete()

        options_to_create = []

        for q in questions_data:
            q_id = q.pop("id", None)
            options = q.pop("options", [])

            if q_id:
                # Update existing question
                question = instance.questions.get(id=q_id)
                for attr, value in q.items():
                    setattr(question, attr, value)
                question.save()
                # Replace its options
                question.options.all().delete()
            else:
                # Create new question
                question = Question.objects.create(survey=instance, **q)
            
            for opt in options:
                options_to_create.append(QuestionOption(question=question, **opt))
        
        if options_to_create:
            QuestionOption.objects.bulk_create(options_to_create)
        
        return instance