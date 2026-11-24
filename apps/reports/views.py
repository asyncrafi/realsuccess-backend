from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.db.models import Count, Sum
from apps.core.utils.mixins import BaseResponseMixin
from apps.events.models import Event
from apps.tickets.models import Ticket
from apps.resources.models import Resource, UserResourceDownload


class ReportsSummaryMetricsView(BaseResponseMixin, APIView):
    """
    Get executive summary registration & attendance metrics for dashboard & reports.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        total_events = Event.objects.count()
        total_registrations = Ticket.objects.count()
        total_checked_in = Ticket.objects.filter(check_in_status="Checked In").count()
        total_resources = Resource.objects.count()

        check_in_rate = round((total_checked_in / total_registrations * 100), 1) if total_registrations > 0 else 0.0
        resources_per_event = round(total_resources / total_events, 1) if total_events > 0 else 0.0

        data = {
            "totalRegistrations": total_registrations,
            "registrationGrowth": 0.0,
            "totalCheckedIn": total_checked_in,
            "checkInRate": check_in_rate,
            "totalEvents": total_events,
            "resourcesPerEvent": resources_per_event,
        }
        return self.success_response(data=data, message="Summary metrics retrieved successfully")


class AttendanceOverviewView(BaseResponseMixin, APIView):
    """
    Get monthly attendance and ticket registration overview dataset for charts.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        data = [
            {"month": m, "ticketAmountGrowth": 0, "checkedInAmountGrowth": 0}
            for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        ]
        return self.success_response(data=data, message="Attendance overview retrieved successfully")


class MonthlyGrowthView(BaseResponseMixin, APIView):
    """
    Get monthly registration & attendance growth dataset.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        data = []
        return self.success_response(data=data, message="Monthly growth retrieved successfully")


class ResourceEventBreakdownView(BaseResponseMixin, APIView):
    """
    Get resources and download metrics per event.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        events = Event.objects.all()
        breakdown = []
        for ev in events:
            res_qs = Resource.objects.filter(event=ev)
            count = res_qs.count()
            dl_sum = res_qs.aggregate(total=Sum("download_count"))["total"] or 0
            popular = res_qs.order_by("-download_count").first()
            breakdown.append({
                "eventName": ev.name,
                "totalResources": count,
                "totalDownloads": dl_sum,
                "mostPopularAsset": popular.title if popular else "N/A",
                "avgEngagementScore": 0.0,
            })

        return self.success_response(data=breakdown, message="Resource event breakdown retrieved successfully")


class DashboardStatsView(BaseResponseMixin, APIView):
    """
    Get high-level summary cards for the admin dashboard home.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        events_count = Event.objects.count()
        tickets_count = Ticket.objects.count()
        checked_in_count = Ticket.objects.filter(check_in_status="Checked In").count()

        stats = [
            {
                "id": "events",
                "title": "Total Events",
                "value": str(events_count),
                "change": "+0 this month",
                "changeType": "positive",
            },
            {
                "id": "tickets",
                "title": "Total Tickets",
                "value": f"{tickets_count:,}",
                "change": "+0.0%",
                "changeType": "positive",
            },
            {
                "id": "attendees",
                "title": "Registered Attendees",
                "value": f"{tickets_count:,}",
                "change": "+0.0%",
                "changeType": "positive",
            },
            {
                "id": "checked_in",
                "title": "Checked In",
                "value": f"{checked_in_count:,}",
                "change": "+0.0%",
                "changeType": "positive",
            },
        ]
        return self.success_response(data=stats, message="Dashboard stats retrieved successfully")
