from django.urls import path
from .views import (
    SessionListCreateView,
    SessionDetailView,
    SessionBookmarkToggleView,
    MyScheduleView,
    SpeakerListCreateView,
    SpeakerDetailView,
)

urlpatterns = [
    # Sessions
    path("sessions/", SessionListCreateView.as_view(), name="session-list-create"),
    path("sessions/my-schedule/", MyScheduleView.as_view(), name="session-my-schedule"),
    path("sessions/<int:pk>/", SessionDetailView.as_view(), name="session-detail"),
    path("sessions/<int:pk>/bookmark/", SessionBookmarkToggleView.as_view(), name="session-bookmark-toggle"),

    # Speakers
    path("speakers/", SpeakerListCreateView.as_view(), name="speaker-list-create"),
    path("speakers/<int:pk>/", SpeakerDetailView.as_view(), name="speaker-detail"),
]
