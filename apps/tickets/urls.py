from django.urls import path
from .views import (
    TicketListCreateView,
    TicketDetailView,
    TicketCheckInView,
    TicketPaymentStatusUpdateView,
    TicketScanValidateView,
    MyTicketView,
    AttendeeListView,
    AttendeeDetailView,
)

urlpatterns = [
    # Tickets
    path("", TicketListCreateView.as_view(), name="ticket-list-create"),
    path("my-ticket/", MyTicketView.as_view(), name="ticket-my-ticket"),
    path("scan/", TicketScanValidateView.as_view(), name="ticket-scan-validate"),
    path("check-in/", TicketCheckInView.as_view(), name="ticket-check-in-post"),
    path("<int:pk>/", TicketDetailView.as_view(), name="ticket-detail"),
    path("<int:pk>/payment-status/", TicketPaymentStatusUpdateView.as_view(), name="ticket-payment-status"),
    path("<int:pk>/check-in/", TicketCheckInView.as_view(), name="ticket-check-in"),

    # Attendees (Admin view)
    path("attendees/", AttendeeListView.as_view(), name="attendee-list"),
    path("attendees/<int:pk>/", AttendeeDetailView.as_view(), name="attendee-detail"),
]
