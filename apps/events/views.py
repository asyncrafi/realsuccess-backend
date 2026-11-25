from rest_framework import generics, status, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.core.utils.mixins import BaseResponseMixin
from .models import Event, EventStory
from .serializers import (
    EventSerializer,
    EventDetailSerializer,
    EventStorySerializer,
    VerifyAccessCodeSerializer,
    EventQRRegisterSerializer,
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
        event_datetime = event.start_datetime
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

            # Cache the verified event for the client's IP so subsequent auth calls resolve the event
            from apps.accounts.utils.event_auth_helpers import get_client_ip
            from django.core.cache import cache
            client_ip = get_client_ip(request)
            if client_ip:
                cache.set(f"last_event_code_{client_ip}", event.access_code, timeout=3600)
                cache.set(f"last_event_id_{client_ip}", event.id, timeout=3600)

            return self.success_response(
                data={
                    "event_id": event.id,
                    "event_name": event.name,
                    "venue": event.venue,
                    "status": event.status,
                    "price": str(event.price),
                    "is_free": event.is_free,
                    "price_display": "Free" if event.is_free else f"${event.price:,.2f}",
                    "qr_registration_token": event.qr_registration_token,
                    "start_date": event.start_date.isoformat(),
                    "end_date": event.end_date.isoformat(),
                    "start_time": event.start_time.strftime("%H:%M:%S") if event.start_time else "09:00:00",
                    "end_time": event.end_time.strftime("%H:%M:%S") if event.end_time else "17:00:00",
                    "check_in_early_minutes": event.check_in_early_minutes,
                    "check_in_time": event.check_in_time.strftime("%H:%M:%S"),
                    "check_in_time_display": event.check_in_time.strftime("%I:%M %p").lstrip("0"),
                    "is_check_in_open": event.is_check_in_open,
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


class EventByQRTokenView(BaseResponseMixin, generics.GenericAPIView):
    """
    Mobile Event QR Scan Endpoint:
    Resolves an Event from its unique qr_registration_token (EVT-...) or access_code
    and returns full event details including price.
    Rejects Ticket QR codes (TKT-...) to enforce separation between Event QR and Ticket QR.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        clean_token = (token or "").strip()
        if clean_token.upper().startswith("TKT-") or clean_token.upper().startswith("REALSUCCESS_TICKET:"):
            return self.error_response(
                message="This is an individual entry ticket QR code, not an event registration QR code.",
                error_code="INVALID_EVENT_QR",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Support full URL or raw token
        if "/" in clean_token:
            clean_token = clean_token.rstrip("/").split("/")[-1]

        event = (
            Event.objects.filter(qr_registration_token__iexact=clean_token).first()
            or Event.objects.filter(access_code__iexact=clean_token).first()
        )
        if not event:
            return self.error_response(
                message="Event not found for this QR code.",
                error_code="EVENT_NOT_FOUND",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer = EventDetailSerializer(event)
        return self.success_response(data=serializer.data, message="Event details retrieved successfully")


class EventQRRegisterView(BaseResponseMixin, generics.GenericAPIView):
    """
    Event Registration Endpoint (via Event QR scan or event_id):
    Creates a unique individual Ticket for the user & event.
    - Free events -> payment_status='Paid', registration_status='Confirmed'
    - Paid events -> payment_status='Pending Payment', registration_status='Pending'
    Prevents duplicate registrations for the same user/email and event.
    """
    serializer_class = EventQRRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        token = (data.get("qr_registration_token") or "").strip()
        if token.upper().startswith("TKT-") or token.upper().startswith("REALSUCCESS_TICKET:"):
            return self.error_response(
                message="Cannot register using a ticket entry QR code. Please scan the event QR code.",
                error_code="INVALID_EVENT_QR",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if "/" in token:
            token = token.rstrip("/").split("/")[-1]

        event = None
        if token:
            event = (
                Event.objects.filter(qr_registration_token__iexact=token).first()
                or Event.objects.filter(access_code__iexact=token).first()
            )
        elif data.get("event_id"):
            event = Event.objects.filter(id=data["event_id"]).first()
        elif data.get("access_code"):
            event = Event.objects.filter(access_code__iexact=data["access_code"].strip()).first()

        if not event:
            return self.error_response(
                message="Event not found. Please scan a valid event QR code.",
                error_code="EVENT_NOT_FOUND",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        User = get_user_model()
        auth_user = request.user if request.user.is_authenticated else None
        email = (data.get("email") or (auth_user.email if auth_user else "")).strip().lower()

        if not email:
            return self.error_response(
                message="Email is required to register for this event.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if not auth_user:
            auth_user = User.objects.filter(email__iexact=email).first()

        profile_name = ""
        if auth_user and hasattr(auth_user, "profile") and auth_user.profile and getattr(auth_user.profile, "name", None):
            profile_name = auth_user.profile.name
        attendee_name = (data.get("name") or profile_name or email.split("@")[0].replace(".", " ").capitalize()).strip()
        attendee_phone = (data.get("phone") or "").strip()
        ticket_type = data.get("ticket_type") or "General"

        from apps.tickets.models import Ticket
        from apps.tickets.serializers import MyTicketDetailSerializer

        with transaction.atomic():
            existing = Ticket.objects.filter(event=event, attendee_email__iexact=email).first()
            if not existing and auth_user:
                existing = Ticket.objects.filter(event=event, user=auth_user).first()

            if existing:
                return self.success_response(
                    data={
                        "already_registered": True,
                        "ticket": MyTicketDetailSerializer(existing).data,
                    },
                    message="You are already registered for this event.",
                    status_code=status.HTTP_200_OK,
                )

            payment_status = "Paid" if event.is_free else "Pending Payment"
            ticket = Ticket.objects.create(
                event=event,
                user=auth_user,
                attendee_name=attendee_name,
                attendee_email=email,
                attendee_phone=attendee_phone,
                ticket_type=ticket_type,
                payment_status=payment_status,
                ticket_status="Unused",
                access_code=event.access_code,
                price_amount=event.price,
            )

        return self.created_response(
            data={
                "already_registered": False,
                "ticket": MyTicketDetailSerializer(ticket).data,
            },
            message=(
                "Registration confirmed! Your free ticket is ready."
                if event.is_free
                else "Registration successful! Ticket created with Pending Payment status."
            ),
        )
