from django.contrib import admin
from django.utils.html import format_html
from .models import (
    QuestionType,
    DeviceType,
    Survey,
    Question,
    QuestionOption,
    Response,
    Answer,
    AuditLog,
    EntityType,
)


# ── Question Option Inline ────────────────────────────────────
class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 0
    fields = ("option_text", "option_value", "display_order", "is_other", "score_weight")
    ordering = ("display_order",)


# ── Question Inline ───────────────────────────────────────────
class QuestionInline(admin.StackedInline):
    model = Question
    extra = 0
    fields = ("question_text", "type", "display_order", "is_required", "min_value", "max_value", "max_length")
    ordering = ("display_order",)
    show_change_link = True


# ── Answer Inline ─────────────────────────────────────────────
class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    fields = ("question", "answer_text", "answer_number", "answer_date", "answer_json", "was_skipped")
    readonly_fields = ("question",)


# ── Survey ────────────────────────────────────────────────────
@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "created_by",
        "status",
        "allow_anonymous",
        "offline_enabled",
        "response_limit",
        "published_at",
        "scheduled_publish_at",
        "scheduled_closed_at",
        "closes_at",
        "created_at",
    )
    list_filter       = ("status", "allow_anonymous", "offline_enabled", "one_response_per_user")
    search_fields     = ("title", "description", "created_by__email")
    readonly_fields   = ("published_at", "created_at", "updated_at")
    ordering          = ("-created_at",)
    inlines           = [QuestionInline]
    fieldsets = (
        ("Basic Info", {
            "fields": ("title", "description", "created_by", "status")
        }),
        ("Settings", {
            "fields": (
                "offline_enabled",
                "allow_anonymous",
                "one_response_per_user",
                "show_progress_bar",
                "response_limit",
            )
        }),
        ("Schedule", {
            "fields": (
                "scheduled_publish_at",
                "scheduled_closed_at",
                "closes_at",
            )
        }),
        ("Timestamps", {
            "fields": ("published_at", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


# ── Question ──────────────────────────────────────────────────
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display    = ("question_text", "survey", "type", "display_order", "is_required")
    list_filter     = ("type", "is_required")
    search_fields   = ("question_text", "survey__title")
    ordering        = ("survey", "display_order")
    inlines         = [QuestionOptionInline]
    fieldsets = (
        ("Question", {
            "fields": ("survey", "type", "question_text", "helper_text", "image_url")
        }),
        ("Settings", {
            "fields": ("display_order", "is_required", "min_value", "max_value", "max_length")
        }),
    )


# ── Question Option ───────────────────────────────────────────
@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display    = ("option_text", "option_value", "question", "display_order", "is_other", "score_weight")
    list_filter     = ("is_other",)
    search_fields   = ("option_text", "option_value", "question__question_text")
    ordering        = ("question", "display_order")
    autocomplete_fields = ("question",)


# ── Question Type ─────────────────────────────────────────────
@admin.register(QuestionType)
class QuestionTypeAdmin(admin.ModelAdmin):
    list_display    = ("code", "name")
    search_fields   = ("code", "name")
    ordering        = ("code",)


# ── Device Type ───────────────────────────────────────────────
@admin.register(DeviceType)
class DeviceTypeAdmin(admin.ModelAdmin):
    list_display    = ("code", "name")
    search_fields   = ("code", "name")
    ordering        = ("code",)


# ── Response ──────────────────────────────────────────────────
@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = (
        "survey",
        "submitted_by",
        "status",
        "device_type",
        "duration_seconds",
        "is_flagged",
        "is_offline_submitted",
        "submitted_at",
    )
    list_filter     = ("status", "is_flagged", "is_offline_submitted", "device_type")
    search_fields   = ("survey__title", "submitted_by__email", "flag_reason")
    readonly_fields = ("submitted_at", "synced_at", "ip_address", "created_at")
    ordering        = ("-submitted_at",)
    inlines         = [AnswerInline]
    fieldsets = (
        ("Response", {
            "fields": ("survey", "submitted_by", "device_type", "status")
        }),
        ("Flags", {
            "fields": ("is_flagged", "flag_reason")
        }),
        ("Meta", {
            "fields": (
                "duration_seconds",
                "is_offline_submitted",
                "synced_at",
                "submitted_at",
                "ip_address",
                "created_at",
            ),
            "classes": ("collapse",),
        }),
    )


# ── Answer ────────────────────────────────────────────────────
@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display    = ("response", "question", "answer_text", "answer_number", "was_skipped")
    list_filter     = ("was_skipped",)
    search_fields   = ("response__survey__title", "question__question_text", "answer_text")
    readonly_fields = ("created_at",)


# ── Audit Log ─────────────────────────────────────────────────
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display    = ("user", "entity", "entity_target_id", "action", "ip_address", "created_at")
    list_filter     = ("action", "entity")
    search_fields   = ("user__email", "entity__name", "ip_address")
    readonly_fields = ("user", "entity", "entity_target_id", "action", "old_values", "new_values", "ip_address", "created_at")
    ordering        = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ── Entity Type ───────────────────────────────────────────────
@admin.register(EntityType)
class EntityTypeAdmin(admin.ModelAdmin):
    list_display    = ("name",)
    search_fields   = ("name",)