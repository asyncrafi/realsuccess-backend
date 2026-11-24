from django.contrib import admin
from apps.core.utils.admin_csv import ExportCsvMixin
from .models import Speaker, Session, SessionResource, SessionBookmark


class SessionResourceInline(admin.TabularInline):
    model = SessionResource
    extra = 1


@admin.register(Speaker)
class SpeakerAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ("name", "role", "organization", "industry", "is_keynote_spotlight")
    list_filter = ("is_keynote_spotlight", "industry")
    search_fields = ("name", "role", "organization")


@admin.register(Session)
class SessionAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ("session_title", "event", "day_number", "date", "time", "type", "status", "speaker")
    list_filter = ("event", "day_number", "type", "status", "date")
    search_fields = ("session_title", "speaker__name", "venue")
    inlines = [SessionResourceInline]


@admin.register(SessionBookmark)
class SessionBookmarkAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ("user", "session", "created_at")
    list_filter = ("session__event",)
    search_fields = ("user__email", "session__session_title")
