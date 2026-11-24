from django.urls import path
from .views import (
    AnnouncementListCreateView,
    AnnouncementDetailView,
    LatestAnnouncementView,
)

urlpatterns = [
    path("", AnnouncementListCreateView.as_view(), name="announcement-list-create"),
    path("latest/", LatestAnnouncementView.as_view(), name="announcement-latest"),
    path("<int:pk>/", AnnouncementDetailView.as_view(), name="announcement-detail"),
]
