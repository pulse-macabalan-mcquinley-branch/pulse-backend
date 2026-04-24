from core.models import SoftDeleteModel, BaseModel
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

class Survey(SoftDeleteModel):

    class Status(models.TextChoices):
        DRAFT       = "draft",      _("Draft")
        PUBLISHED   = "published",  _("Published")
        CLOSED      = "closed",     _("Closed")
        ARCHIVED    = "archived",   _("Archived")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="surveys",
    )

    title = models.CharField(
        max_length=255,
    )
    description = models.TextField(
        max_length=1000,
        null=True,
        blank=True,
        help_text= "Respondent-facing intro"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True
    )

    offline_enabled = models.BooleanField(
        default=False,
        help_text= "PWA offline mode"
    )
    allow_anonymous = models.BooleanField(
        default=False,
        help_text= "No login required"
    )

    response_limit = models.PositiveIntegerField(
        default=1,
        null=True,
        help_text = "Max allowed responses, null = unlimited"
    )

    show_progress_bar = models.BooleanField(
        default=False,
        help_text= "UX setting"
    )
    one_response_per_user = models.BooleanField(
        default=False,
        help_text="Dedup control"
    )

    published_at = models.DateTimeField(null=True, blank=True)
    closes_at = models.DateTimeField(null=True, blank=True, help_text="Auto-close schedule")


class QuestionType(SoftDeleteModel):
    code = models.CharField(
        unique=True,
        max_length=50,
    )
    name = models.CharField(
        unique=True,
        max_length=50,
    )

class Question(SoftDeleteModel):

    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name="questions",
        db_index=True,
    )
    type = models.ForeignKey(
        QuestionType,
        on_delete=models.CASCADE,
        related_name="questions"
    )

    question_text = models.TextField(
        max_length=500,
    )
    helper_text = models.TextField(
        max_length=500,
        null=True,
        blank=True
    )

    display_order = models.IntegerField(
        default=0,
        db_index=True
    )
    
    is_required = models.BooleanField(
        default=True
    )

    min_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Minimum allowed value for numeric/rating questions"
    )

    max_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MaxValueValidator(100)],
        help_text="Maximum allowed value for numeric/rating questions"
    )

    max_length = models.IntegerField(
        default=200,
        null=True,
        blank=True,
        help_text="Text field character limit"
    )

    image_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text= "Optional question image"
    )

class QuestionOption(SoftDeleteModel):
    question = models.ForeignKey(
        Question,
        db_index=True,
        related_name="options",
        on_delete=models.CASCADE
    )
    option_text = models.CharField(
        max_length=500,
    )
    option_value = models.CharField(
        max_length=100,
        help_text="Stored answer code, e.g. 'employed_private'"
    )
    display_order = models.IntegerField(
        default=0,
        db_index=True
    )
    is_other = models.BooleanField(
        default=False,
        help_text="If True, renders an open text input alongside this option"
    )
    image_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Optional image for visual choice questions"
    )
    score_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Used for scored assessments or quizzes"
    )

    class Meta:
        ordering = ["display_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["question", "option_value"],
                name="unique_option_value_per_question"
            )
        ]
        
    def __str__(self):
        return f"{self.question} → {self.option_text}"

class DeviceType(SoftDeleteModel):
    code = models.CharField(
        max_length=50,
        unique=True,
    )
    name = models.CharField(
        max_length=50,
        unique=True,
    )

class Response(SoftDeleteModel):

    class Status(models.TextChoices):
        PARTIAL     = "partial",    _("Partial")
        COMPLETE    = "complete",   _("Complete")
        FLAGGED     = "flagged",    _("Flagged")
        REJECTED    = "rejected",   _("Rejected")

    survey = models.ForeignKey(
        Survey,
        db_index=True,
        related_name="responses",
        on_delete=models.CASCADE
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="responses",
        help_text="USER.id, nullable if anonymous"
    )
    device_type = models.ForeignKey(
        DeviceType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="responses",
        help_text="Type of device use in this response"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PARTIAL,
        db_index=True,
    )

    ip_address = models.GenericIPAddressField(
        protocol='both',
        unpack_ipv4=False,
        null=True,
        blank=True,
    )

    duration_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Time taken to complete the survey/response in seconds"
    )

    is_flagged = models.BooleanField(
        default=False,
    )
    flag_reason = models.TextField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Straight-lining, duplicate, etc."
    )

    is_offline_submitted = models.BooleanField(
        default=False,
    )

    synced_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)


class Answer(BaseModel):

    response = models.ForeignKey(
        Response,
        on_delete=models.SET_NULL,
        related_name="answers",
        db_index=True,
        null=True,
        blank=True
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="responses",
    )

    answer_text = models.TextField(
        max_length=1000,
        null=True,
        blank=True,
        help_text="Open-ended or 'other' text"
    )
    answer_number = models.DecimalField(
        decimal_places= 2,
        max_digits=10,
        null=True,
        blank=True,
        help_text="Numeric / rating response"
    )
    answer_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date-type question"
    )
    answer_json = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Stores answers to questions in JSON format, keyed by question id or code"
    )
    file_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
    )

    was_skipped = models.BooleanField(
        default=False,
    )

class EntityType(BaseModel):
    name = models.CharField(
        max_length=50,
        unique=True,
    )

class AuditLog(BaseModel):

    class Action(models.TextChoices):
        CREATED = "created", _("Created")
        UPDATED = "updated", _("Updated")
        DELETED = "deleted", _("Created")
        PUBLISHED = "published", _("Published")
        EXPORTED = "exported", _("Exported")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
        related_name="logs"
    )
    entity = models.ForeignKey(
        EntityType,
        on_delete=models.CASCADE,
        related_name="logs",
        db_index=True,
        null=True, 
        blank=True,
        help_text="survey, question, response, user…"
    )
    entity_target_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="ID of affected record",
        editable=False,
    )
    action = models.CharField(
        max_length=50,
        choices=Action.choices,
    )

    old_values = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="Snapshot before change"
    )
    new_values = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="	Snapshot after change"
    )

    ip_address = models.GenericIPAddressField(
        protocol='both',
        unpack_ipv4=False,
        null=True,
        blank=True,
    )

