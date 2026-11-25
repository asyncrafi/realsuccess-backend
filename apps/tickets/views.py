from rest_framework import generics, status, permissions, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from apps.core.utils.mixins import BaseResponseMixin
from .models import Ticket
from .serializers import (
    TicketSerializer,
    TicketPaymentStatusSerializer,
    TicketScanSerializer,
    AttendeeSerializer,
    MyTicketDetailSerializer,
)


class TicketListCreateView(BaseResponseMixin, generics.ListCreateAPIView):
    queryset = Ticket.objects.select_related("event", "checked_in_by", "user").all()
    serializer_class = TicketSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["event", "ticket_type", "payment_status", "ticket_status", "registration_status", "check_in_status"]
    search_fields = ["ticket_id", "attendee_name", "attendee_email", "event__name", "qr_validation_token"]
    ordering_fields = ["created_at", "issue_date", "attendee_name"]
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
        ticket = serializer.save()
        return self.created_response(data=self.get_serializer(ticket).data, message="Ticket issued successfully")


class TicketDetailView(BaseResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Ticket.objects.select_related("event", "checked_in_by", "user").all()
    serializer_class = TicketSerializer
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
        return self.updated_response(data=serializer.data, message="Ticket updated successfully")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return self.deleted_response(message="Ticket deleted successfully")


class TicketPaymentStatusUpdateView(BaseResponseMixin, generics.GenericAPIView):
    """
    Admin Endpoint: Manually verify or reject a ticket's payment status.
    Requires authenticated staff/admin user.
    """
    serializer_class = TicketPaymentStatusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        if not request.user.is_staff:
            return self.error_response(
                message="Only authorized event admins can update payment status.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        ticket = get_object_or_404(Ticket, pk=pk)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_payment_status = serializer.validated_data["payment_status"]
        ticket.payment_status = new_payment_status
        if new_payment_status == "Payment Rejected":
            ticket.ticket_status = "Cancelled"
        elif new_payment_status == "Paid" and ticket.ticket_status == "Cancelled":
            ticket.ticket_status = "Unused"
        ticket.save()

        return self.updated_response(
            data=TicketSerializer(ticket).data,
            message=f"Ticket payment status updated to {new_payment_status}",
        )

    def post(self, request, pk):
        return self.patch(request, pk)


class TicketScanValidateView(BaseResponseMixin, generics.GenericAPIView):
    """
    Admin Entrance Scanner Endpoint:
    Atomically validates an individual Ticket QR (TKT-... or ticket_id)
    against payment status, event match, cancellation, and duplicate usage.
    """
    serializer_class = TicketScanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.is_staff:
            return self.error_response(
                message="Only authorized event staff can scan tickets.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        raw_token = serializer.validated_data["qr_token"].strip()
        event_id = serializer.validated_data.get("event_id")

        # Enforce separation: Event registration QR cannot be used for entrance
        if raw_token.upper().startswith("EVT-") or "realsuccess://event/" in raw_token.lower():
            return self.error_response(
                message="Invalid Ticket: This is an event registration QR code, not an entry ticket.",
                error_code="INVALID_TICKET",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        clean_token = raw_token.replace("REALSUCCESS_TICKET:", "").strip()

        with transaction.atomic():
            ticket = (
                Ticket.objects.select_for_update(of=("self",))
                .select_related("event", "checked_in_by")
                .filter(
                    Q(qr_validation_token__iexact=clean_token)
                    | Q(ticket_id__iexact=clean_token)
                    | Q(qr_code_data__iexact=raw_token)
                )
                .first()
            )

            if not ticket:
                return Response(
                    {
                        "success": False,
                        "valid": False,
                        "scan_status": "INVALID_TICKET",
                        "message": "Invalid Ticket",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            if event_id and ticket.event_id != int(event_id):
                return Response(
                    {
                        "success": False,
                        "valid": False,
                        "scan_status": "INVALID_TICKET",
                        "message": "Invalid Ticket: Ticket belongs to a different event.",
                        "ticket": TicketSerializer(ticket).data,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if ticket.ticket_status == "Cancelled" or ticket.registration_status == "Cancelled":
                return Response(
                    {
                        "success": False,
                        "valid": False,
                        "scan_status": "CANCELLED",
                        "message": "Ticket Cancelled",
                        "ticket": TicketSerializer(ticket).data,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if ticket.payment_status != "Paid":
                return Response(
                    {
                        "success": False,
                        "valid": False,
                        "scan_status": "PAYMENT_NOT_CONFIRMED",
                        "message": "Payment Not Confirmed",
                        "ticket": TicketSerializer(ticket).data,
                    },
                    status=status.HTTP_402_PAYMENT_REQUIRED,
                )

            if ticket.ticket_status == "Used" or ticket.check_in_status == "Checked In":
                return Response(
                    {
                        "success": False,
                        "valid": False,
                        "scan_status": "ALREADY_USED",
                        "message": "Already Used",
                        "checked_in_at": ticket.checked_in_at.isoformat() if ticket.checked_in_at else None,
                        "ticket": TicketSerializer(ticket).data,
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            # Valid, Paid, and Unused -> Check in atomically!
            ticket.check_in(staff_user=request.user)

        return Response(
            {
                "success": True,
                "valid": True,
                "scan_status": "APPROVED",
                "message": "Approved / Entry Allowed",
                "ticket": TicketSerializer(ticket).data,
            },
            status=status.HTTP_200_OK,
        )


class TicketCheckInView(BaseResponseMixin, generics.GenericAPIView):
    """
    Legacy Check-in endpoint (enforces payment validation too).
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk=None):
        with transaction.atomic():
            if pk:
                ticket = get_object_or_404(Ticket.objects.select_for_update(), pk=pk)
            else:
                ticket_id = request.data.get("ticket_id")
                ticket = get_object_or_404(Ticket.objects.select_for_update(), ticket_id=ticket_id)

            if ticket.payment_status != "Paid":
                return self.error_response(
                    message="Payment Not Confirmed",
                    error_code="PAYMENT_NOT_CONFIRMED",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            if ticket.ticket_status == "Used":
                return self.error_response(
                    message="Already Used",
                    error_code="ALREADY_USED",
                    status_code=status.HTTP_409_CONFLICT,
                )

            ticket.check_in(staff_user=request.user if request.user.is_authenticated else None)

        return self.success_response(
            data=TicketSerializer(ticket).data,
            message=f"Attendee {ticket.attendee_name} successfully checked in!",
        )


class MyTicketView(BaseResponseMixin, generics.GenericAPIView):
    """
    Mobile My Event Ticket screen:
    Retrieves the ticket(s) for the authenticated user, or via event_id / access_code / email.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        event_id = request.query_params.get("event_id")
        access_code = request.query_params.get("access_code")
        email = request.query_params.get("email")

        qs = Ticket.objects.select_related("event").all()
        if event_id:
            qs = qs.filter(event_id=event_id)
        elif access_code:
            qs = qs.filter(Q(access_code__iexact=access_code) | Q(event__access_code__iexact=access_code))

        ticket = None
        if request.user.is_authenticated:
            ticket = qs.filter(user=request.user).first() or qs.filter(attendee_email__iexact=request.user.email).first()

        if not ticket and email:
            ticket = qs.filter(attendee_email__iexact=email).first()

        if not ticket and (event_id or access_code) and not request.user.is_authenticated:
            ticket = qs.first()

        if not ticket:
            return self.not_found_response(message="No ticket found for this account.")

        serializer = MyTicketDetailSerializer(ticket)
        return self.success_response(data=serializer.data, message="My ticket retrieved successfully")


class AttendeeListView(BaseResponseMixin, generics.ListAPIView):
    """
    Admin Dashboard Attendee Management endpoint
    """
    queryset = Ticket.objects.select_related("event").all()
    serializer_class = AttendeeSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["event", "ticket_type", "payment_status", "ticket_status", "registration_status", "check_in_status"]
    search_fields = ["attendee_name", "attendee_email", "access_code", "event__name", "attendee_phone"]
    ordering_fields = ["created_at", "attendee_name"]
    ordering = ["-created_at"]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return self.success_response(data=serializer.data)


class AttendeeDetailView(BaseResponseMixin, generics.RetrieveUpdateAPIView):
    queryset = Ticket.objects.all()
    serializer_class = AttendeeSerializer
    permission_classes = [permissions.AllowAny]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.success_response(data=serializer.data)
