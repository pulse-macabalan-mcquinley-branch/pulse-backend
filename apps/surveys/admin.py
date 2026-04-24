from django.contrib import admin
from .models import (
    QuestionType,
    DeviceType,
    QuestionOption
)

@admin.register(QuestionType)
class QuestionTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "name",)
    search_fields = ("code", "name",)

@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ("question", "option_text",)