from django.contrib import admin
from .models import (
    QuestionType,
    DeviceType,
    QuestionOption,
    Survey,
)

@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ("title",)

@admin.register(QuestionType)
class QuestionTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "name",)
    search_fields = ("code", "name",)

@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ("question", "option_text",)