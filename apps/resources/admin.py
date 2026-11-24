from django.contrib import admin
from apps.core.utils.admin_csv import ExportCsvMixin
from .models import Resource, UserResourceDownload


@admin.register(Resource)
class ResourceAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ("title", "event", "type", "category", "status", "file_size", "is_featured", "download_count", "created_at")
    list_filter = ("event", "type", "category", "status", "is_featured")
    search_fields = ("title", "description", "category")


@admin.register(UserResourceDownload)
class UserResourceDownloadAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ("user", "resource", "downloaded_at")
    list_filter = ("resource__event",)
    search_fields = ("user__email", "resource__title")
