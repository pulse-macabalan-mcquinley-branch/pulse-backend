from rest_framework import serializers
from ..models import Answer, Response, Survey
from apps.users.serializers import UserSerializer
from .base import DeviceTypeSerializer
from .question import QuestionSerializer


class AnswerSerializer(serializers.ModelSerializer):
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
        read_only_fields = ["id", "created_at"]


class AnswerWriteSerializer(serializers.ModelSerializer):
    question_id = serializers.UUIDField()

    class Meta:
        model = Answer
        fields = [
            "question_id",
            "answer_text",
            "answer_number",
            "answer_date",
            "answer_json",
            "file_url",
            "was_skipped",
        ]

    def validate(self, attrs):
        from ..models import Question
        question_id = attrs.get("question_id")
        was_skipped = attrs.get("was_skipped", False)

        try:
            question = Question.objects.select_related("type").get(id=question_id)
        except Question.DoesNotExist:
            raise serializers.ValidationError({
                "question_id": "Question does not exist."
            })

        # ── Required question must not be skipped ─────────────
        if question.is_required and was_skipped:
            raise serializers.ValidationError({
                "was_skipped": f"Question '{question.question_text}' is required."
            })

        # ── Must provide a value if not skipped ───────────────
        if not was_skipped:
            code = question.type.code.lower()
            has_value = any([
                attrs.get("answer_text"),
                attrs.get("answer_number") is not None,
                attrs.get("answer_date"),
                attrs.get("answer_json"),
                attrs.get("file_url"),
            ])
            if not has_value:
                raise serializers.ValidationError({
                    "answer": f"Question '{question.question_text}' requires an answer."
                })

        return attrs


class ResponseSerializer(serializers.ModelSerializer):
    submitted_by = UserSerializer(read_only=True)
    device_type  = DeviceTypeSerializer(read_only=True)
    answers      = AnswerSerializer(many=True, read_only=True)

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
            "answers",
        ]
        read_only_fields = ["id", "created_at"]


class ResponseSubmitSerializer(serializers.ModelSerializer):
    answers         = AnswerWriteSerializer(many=True, required=True)
    device_type_id  = serializers.PrimaryKeyRelatedField(
        queryset=__import__('apps.surveys.models', fromlist=['DeviceType']).DeviceType.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Response
        fields = [
            "answers",
            "device_type_id",
            "duration_seconds",
            "is_offline_submitted",
            "synced_at",
        ]

    def validate_answers(self, value):
        if not value:
            raise serializers.ValidationError("At least one answer is required.")
        return value

    def create(self, validated_data):
        from django.utils import timezone
        from ..models import Answer, Question

        answers_data   = validated_data.pop("answers")
        device_type    = validated_data.pop("device_type_id", None)
        survey         = self.context["survey"]
        request        = self.context["request"]

        # ── Check response limit ──────────────────────────────
        if survey.response_limit:
            current_count = Response.objects.filter(
                survey=survey,
                status=Response.Status.COMPLETE,
            ).count()
            if current_count >= survey.response_limit:
                raise serializers.ValidationError(
                    "This survey has reached its response limit."
                )

        # ── Check one_response_per_user ───────────────────────
        if survey.one_response_per_user and request.user.is_authenticated:
            already_responded = Response.objects.filter(
                survey=survey,
                submitted_by=request.user,
                status=Response.Status.COMPLETE,
            ).exists()
            if already_responded:
                raise serializers.ValidationError(
                    "You have already submitted a response to this survey."
                )

        # ── Create response ───────────────────────────────────
        response = Response.objects.create(
            survey=survey,
            submitted_by=request.user if request.user.is_authenticated else None,
            device_type=device_type,
            status=Response.Status.COMPLETE,
            submitted_at=timezone.now(),
            ip_address=request.META.get("REMOTE_ADDR"),
            **validated_data,
        )

        # ── Bulk create answers ───────────────────────────────
        Answer.objects.bulk_create([
            Answer(
                response=response,
                question_id=a["question_id"],
                answer_text=a.get("answer_text"),
                answer_number=a.get("answer_number"),
                answer_date=a.get("answer_date"),
                answer_json=a.get("answer_json"),
                file_url=a.get("file_url"),
                was_skipped=a.get("was_skipped", False),
            )
            for a in answers_data
        ])

        return response