from django.urls import path
from .views import (
    ReportsSummaryMetricsView,
    AttendanceOverviewView,
    MonthlyGrowthView,
    ResourceEventBreakdownView,
    DashboardStatsView,
)

app_name = "reports"

urlpatterns = [
    path("summary/", ReportsSummaryMetricsView.as_view(), name="summary-metrics"),
    path("attendance-overview/", AttendanceOverviewView.as_view(), name="attendance-overview"),
    path("monthly-growth/", MonthlyGrowthView.as_view(), name="monthly-growth"),
    path("resource-breakdown/", ResourceEventBreakdownView.as_view(), name="resource-breakdown"),
    path("dashboard-stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
]
