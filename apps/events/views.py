from rest_framework import generics, status, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from apps.core.utils.mixins import BaseResponseMixin
from .models import Event, EventStory
from .serializers import (
    EventSerializer,
    EventDetailSerializer,
    EventStorySerializer,
    VerifyAccessCodeSerializer,
)


class EventListCreateView(BaseResponseMixin, generics.ListCreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "venue"]
    search_fields = ["name", "venue", "access_code", "description"]
    ordering_fields = ["start_date", "created_at", "name"]
    ordering = ["-start_date"]

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
        event = serializer.save()
        return self.created_response(
            data=self.get_serializer(event).data,
            message="Event created successfully"
        )


class EventDetailView(BaseResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Event.objects.all()
    serializer_class = EventDetailSerializer
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
        return self.updated_response(data=serializer.data, message="Event updated successfully")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return self.deleted_response(message="Event deleted successfully")


class CurrentEventView(BaseResponseMixin, generics.GenericAPIView):
    """
    Mobile Home Screen Endpoint:
    Returns the currently active / nearest upcoming event with live countdown details.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        now = timezone.now().date()
        # Active event first, or nearest upcoming
        event = Event.objects.filter(status="Active").first()
        if not event:
            event = Event.objects.filter(start_date__gte=now).order_by("start_date").first()
        if not event:
            event = Event.objects.first()

        if not event:
            return self.not_found_response(message="No event found")

        serializer = EventDetailSerializer(event)
        data = serializer.data

        # Calculate countdown components
        event_datetime = timezone.make_aware(
            timezone.datetime.combine(event.start_date, timezone.datetime.min.time())
        )
        time_diff = event_datetime - timezone.now()
        total_seconds = max(0, int(time_diff.total_seconds()))

        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        data["countdown"] = {
            "days": f"{days:02d}",
            "hours": f"{hours:02d}",
            "minutes": f"{minutes:02d}",
            "seconds": f"{seconds:02d}",
            "total_seconds": total_seconds,
            "is_live": total_seconds == 0,
        }

        return self.success_response(data=data, message="Current event retrieved successfully")


class VerifyAccessCodeView(BaseResponseMixin, generics.GenericAPIView):
    """
    Mobile Event Access Screen Endpoint:
    Validates the event access code entered by the user (e.g. RS-AUG-2026-001).
    """
    serializer_class = VerifyAccessCodeSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["access_code"].strip()

        try:
            event = Event.objects.get(access_code__iexact=code)
            return self.success_response(
                data={
                    "event_id": event.id,
                    "event_name": event.name,
                    "venue": event.venue,
                    "status": event.status,
                    "start_date": event.start_date.isoformat(),
                    "end_date": event.end_date.isoformat(),
                },
                message="Access code verified successfully"
            )
        except Event.DoesNotExist:
            return self.error_response(
                message="Invalid event access code. Please check your code and try again.",
                error_code="INVALID_ACCESS_CODE",
                status_code=status.HTTP_404_NOT_FOUND
            )


class EventStoryListCreateView(BaseResponseMixin, generics.ListCreateAPIView):
    serializer_class = EventStorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        event_id = self.kwargs.get("event_id")
        return EventStory.objects.filter(event_id=event_id)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return self.success_response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        event_id = self.kwargs.get("event_id")
        event = Event.objects.get(pk=event_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        story = serializer.save(event=event)
        return self.created_response(data=self.get_serializer(story).data)
