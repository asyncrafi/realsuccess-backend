from django.contrib import admin
from apps.core.utils.admin_csv import ExportCsvMixin
from .models import Event, EventStory


class EventStoryInline(admin.TabularInline):
    model = EventStory
    extra = 1


@admin.register(Event)
class EventAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ("name", "access_code", "status", "venue", "start_date", "end_date", "total_tickets")
    list_filter = ("status", "start_date")
    search_fields = ("name", "access_code", "venue")
    inlines = [EventStoryInline]


@admin.register(EventStory)
class EventStoryAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ("title", "event", "duration", "order", "created_at")
    list_filter = ("event",)
    search_fields = ("title", "event__name")
