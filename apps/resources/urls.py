from django.urls import path
from .views import (
    ResourceListCreateView,
    ResourceDetailView,
    ResourceDownloadRecordView,
    FeaturedResourceView,
    RecentDownloadsView,
)

urlpatterns = [
    path("", ResourceListCreateView.as_view(), name="resource-list-create"),
    path("featured/", FeaturedResourceView.as_view(), name="resource-featured"),
    path("recent-downloads/", RecentDownloadsView.as_view(), name="resource-recent-downloads"),
    path("<int:pk>/", ResourceDetailView.as_view(), name="resource-detail"),
    path("<int:pk>/download/", ResourceDownloadRecordView.as_view(), name="resource-download-record"),
]
