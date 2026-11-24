from rest_framework import generics, status, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from apps.core.utils.mixins import BaseResponseMixin
from .models import Session, Speaker, SessionBookmark, SessionResource
from .serializers import (
    SessionListSerializer,
    SessionDetailSerializer,
    SpeakerSerializer,
    SpeakerDetailSerializer,
    SessionResourceSerializer,
)


class SessionListCreateView(BaseResponseMixin, generics.ListCreateAPIView):
    queryset = Session.objects.all()
    serializer_class = SessionListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["event", "day_number", "type", "status", "date"]
    search_fields = ["session_title", "speaker__name", "venue", "description"]
    ordering_fields = ["date", "start_time", "order"]
    ordering = ["date", "start_time"]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return self.success_response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = SessionDetailSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        session = serializer.save()
        return self.created_response(
            data=SessionDetailSerializer(session, context={"request": request}).data,
            message="Session created successfully"
        )


class SessionDetailView(BaseResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Session.objects.all()
    serializer_class = SessionDetailSerializer
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
        return self.updated_response(data=serializer.data, message="Session updated successfully")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return self.deleted_response(message="Session deleted successfully")


class SessionBookmarkToggleView(BaseResponseMixin, generics.GenericAPIView):
    """
    Toggle bookmark for a session on user's schedule.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        session = get_object_or_404(Session, pk=pk)
        bookmark, created = SessionBookmark.objects.get_or_create(user=request.user, session=session)
        if not created:
            bookmark.delete()
            return self.success_response(
                data={"is_bookmarked": False},
                message="Session removed from your schedule"
            )
        return self.success_response(
            data={"is_bookmarked": True},
            message="Session added to your schedule"
        )


class MyScheduleView(BaseResponseMixin, generics.GenericAPIView):
    """
    Mobile My Schedule screen: lists sessions bookmarked by current user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        bookmarked_session_ids = SessionBookmark.objects.filter(
            user=request.user
        ).values_list("session_id", flat=True)
        sessions = Session.objects.filter(id__in=bookmarked_session_ids).order_by("date", "start_time")
        serializer = SessionListSerializer(sessions, many=True, context={"request": request})
        return self.success_response(data=serializer.data, message="My schedule retrieved successfully")


class SpeakerListCreateView(BaseResponseMixin, generics.ListCreateAPIView):
    queryset = Speaker.objects.all()
    serializer_class = SpeakerSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["is_keynote_spotlight"]
    search_fields = ["name", "role", "organization", "industry"]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return self.success_response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        speaker = serializer.save()
        return self.created_response(data=self.get_serializer(speaker).data)


class SpeakerDetailView(BaseResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Speaker.objects.all()
    serializer_class = SpeakerDetailSerializer
    permission_classes = [permissions.AllowAny]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.success_response(data=serializer.data)
