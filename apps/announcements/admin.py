from django.contrib import admin
from apps.core.utils.admin_csv import ExportCsvMixin
from .models import Announcement, AnnouncementAttachment


class AnnouncementAttachmentInline(admin.TabularInline):
    model = AnnouncementAttachment
    extra = 1


@admin.register(Announcement)
class AnnouncementAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ("title", "event", "category", "priority", "status", "published_by", "created_at")
    list_filter = ("event", "priority", "status", "category")
    search_fields = ("title", "content", "published_by")
    inlines = [AnnouncementAttachmentInline]


@admin.register(AnnouncementAttachment)
class AnnouncementAttachmentAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ("name", "announcement", "file_type", "size", "created_at")
    search_fields = ("name", "announcement__title")
