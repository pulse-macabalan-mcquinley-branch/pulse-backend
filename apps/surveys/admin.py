from django.contrib import admin
from .models import (
    QuestionType,
    DeviceType,
)

@admin.register(QuestionType)
class QuestionTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")