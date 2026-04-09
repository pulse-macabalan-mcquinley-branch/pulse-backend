from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Full-featured admin for CustomUser."""

    list_display  = ("email", "full_name", "role", "is_active", "is_staff", "date_joined")
    list_filter   = ("role", "is_active", "is_staff", "date_joined")
    search_fields = ("email", "first_name", "last_name")
    ordering      = ("-date_joined",)
    readonly_fields = ("id", "date_joined", "last_login")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "avatar")}),
        (_("Role & permissions"), {
            "fields": ("role", "is_active", "is_staff", "is_superuser",
                        "groups", "user_permissions"),
        }),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "password1", "password2", "role"),
        }),
    )

    # ── Bulk actions ──────────────────────────────────────────
    actions = ["activate_users", "deactivate_users", "promote_to_admin"]

    @admin.action(description="Activate selected users")
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} user(s) activated.")

    @admin.action(description="Deactivate selected users")
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} user(s) deactivated.")

    @admin.action(description="Promote to admin role")
    def promote_to_admin(self, request, queryset):
        updated = queryset.update(role=CustomUser.Role.ADMIN, is_staff=True)
        self.message_user(request, f"{updated} user(s) promoted to admin.")