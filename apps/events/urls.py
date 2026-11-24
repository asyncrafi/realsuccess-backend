from django.urls import path
from .views import (
    EventListCreateView,
    EventDetailView,
    CurrentEventView,
    VerifyAccessCodeView,
    EventStoryListCreateView,
)

urlpatterns = [
    path("", EventListCreateView.as_view(), name="event-list-create"),
    path("current/", CurrentEventView.as_view(), name="event-current"),
    path("verify-access-code/", VerifyAccessCodeView.as_view(), name="event-verify-access-code"),
    path("<int:pk>/", EventDetailView.as_view(), name="event-detail"),
    path("<int:event_id>/stories/", EventStoryListCreateView.as_view(), name="event-stories"),
]
