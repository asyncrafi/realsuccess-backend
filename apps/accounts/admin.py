from django.contrib import admin
from django.contrib.auth import get_user_model
from apps.core.utils.admin_csv import ExportCsvMixin
from .models import OTP, UserProfile

User = get_user_model()


class CustomUserAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ("email", "is_deleted", "is_active", "is_staff")
    list_filter = ("is_staff", "is_superuser", "is_deleted", "is_blocked")
    fieldsets = (
        (None, {"fields": ("email",)}),
        ("Personal info", {"fields": ("username", "social_auth_provider")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_deleted",
                    "deleted_at",
                    "is_blocked",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    list_editable = ("is_active",)
    search_fields = ("email", "username")
    ordering = ("email",)
    readonly_fields = ("created_at", "updated_at", "last_login")


admin.site.register(User, CustomUserAdmin)


@admin.register(OTP)
class OTPAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ("user", "purpose", "otp", "created_at", "expires_at", "is_used")
    list_filter = ("purpose", "is_used")
    search_fields = ("user__email", "otp")
    readonly_fields = ("created_at", "updated_at")


@admin.register(UserProfile)
class UserProfileAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ("user", "name", "gender", "phone", "last_active")
    search_fields = ("user__email", "user__username", "name", "phone")
    list_filter = ("gender",)
    readonly_fields = ("created_at", "updated_at", "last_active")
