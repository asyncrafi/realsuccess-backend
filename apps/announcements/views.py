from rest_framework import generics, status, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from apps.core.utils.mixins import BaseResponseMixin
from .models import Announcement, AnnouncementAttachment
from .serializers import (
    AnnouncementSerializer,
    AnnouncementDetailSerializer,
    AnnouncementAttachmentSerializer,
)


class AnnouncementListCreateView(BaseResponseMixin, generics.ListCreateAPIView):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["event", "priority", "status", "category"]
    search_fields = ["title", "content", "published_by", "category"]
    ordering_fields = ["created_at", "priority", "title"]
    ordering = ["-created_at"]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return self.success_response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        announcement = serializer.save()
        return self.created_response(
            data=self.get_serializer(announcement).data,
            message="Announcement created successfully"
        )


class AnnouncementDetailView(BaseResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementDetailSerializer
    permission_classes = [permissions.AllowAny]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.success_response(data=serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.updated_response(data=serializer.data, message="Announcement updated successfully")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return self.deleted_response(message="Announcement deleted successfully")


class LatestAnnouncementView(BaseResponseMixin, generics.GenericAPIView):
    """
    Mobile Home Screen / Alert banner: returns the latest published high-priority announcement.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        announcement = Announcement.objects.filter(
            status="Published",
            priority="High Priority"
        ).first()
        if not announcement:
            announcement = Announcement.objects.filter(status="Published").first()

        if not announcement:
            return self.not_found_response(message="No announcement found")

        serializer = AnnouncementDetailSerializer(announcement)
        return self.success_response(data=serializer.data, message="Latest announcement retrieved")
