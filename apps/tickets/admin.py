from django.contrib import admin
from apps.core.utils.admin_csv import ExportCsvMixin
from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = (
        "ticket_id",
        "attendee_name",
        "attendee_email",
        "event",
        "ticket_type",
        "registration_status",
        "check_in_status",
        "access_code",
        "issue_date",
    )
    list_filter = ("event", "ticket_type", "registration_status", "check_in_status", "issue_date")
    search_fields = ("ticket_id", "attendee_name", "attendee_email", "access_code")
    actions = ["mark_as_checked_in"]

    def mark_as_checked_in(self, request, queryset):
        for ticket in queryset:
            ticket.check_in()
        self.message_user(request, f"{queryset.count()} tickets marked as Checked In.")
    mark_as_checked_in.short_description = "Check In Selected Tickets"
