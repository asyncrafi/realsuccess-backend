from rest_framework import serializers
from .models import Ticket
from apps.events.serializers import EventSerializer


class TicketSerializer(serializers.ModelSerializer):
    eventName = serializers.CharField(source="event.name", read_only=True)
    attendeeName = serializers.CharField(source="attendee_name")
    attendeeEmail = serializers.EmailField(source="attendee_email")
    attendeePhone = serializers.CharField(source="attendee_phone", required=False, allow_blank=True)
    ticketType = serializers.CharField(source="ticket_type", required=False)
    paymentStatus = serializers.CharField(source="payment_status", required=False)
    ticketStatus = serializers.CharField(source="ticket_status", required=False)
    checkInStatus = serializers.CharField(source="check_in_status", read_only=True)
    checkedInBy = serializers.SerializerMethodField()
    issueDate = serializers.SerializerMethodField()
    status = serializers.CharField(source="registration_status", read_only=True)
    qrValidationToken = serializers.CharField(source="qr_validation_token", read_only=True)
    priceAmount = serializers.DecimalField(source="price_amount", max_digits=10, decimal_places=2, required=False)
    isFree = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            "id",
            "ticket_id",
            "ticketId",
            "event",
            "eventName",
            "attendeeName",
            "attendeeEmail",
            "attendeePhone",
            "attendee_avatar",
            "ticketType",
            "payment_status",
            "paymentStatus",
            "ticket_status",
            "ticketStatus",
            "checkInStatus",
            "check_in_time_slot",
            "checked_in_at",
            "checkedInBy",
            "access_code",
            "qr_validation_token",
            "qrValidationToken",
            "qr_code_data",
            "price",
            "price_amount",
            "priceAmount",
            "isFree",
            "issueDate",
            "status",
            "created_at",
        ]

    ticketId = serializers.CharField(source="ticket_id", read_only=True)

    def get_issueDate(self, obj):
        if obj.issue_date:
            return obj.issue_date.strftime("%d %B %Y")
        return ""

    def get_checkedInBy(self, obj):
        if obj.checked_in_by:
            return obj.checked_in_by.email
        return None

    def get_isFree(self, obj):
        if obj.event:
            return obj.event.is_free
        return (obj.price_amount or 0) <= 0


class TicketPaymentStatusSerializer(serializers.Serializer):
    payment_status = serializers.ChoiceField(
        choices=["Pending Payment", "Paid", "Payment Rejected"],
        required=True,
    )


class TicketScanSerializer(serializers.Serializer):
    qr_token = serializers.CharField(required=True)
    event_id = serializers.IntegerField(required=False)


class AttendeeSerializer(serializers.ModelSerializer):
    """
    Formatted specifically for Admin Dashboard Attendee Management table
    """
    name = serializers.CharField(source="attendee_name")
    email = serializers.EmailField(source="attendee_email")
    avatar = serializers.SerializerMethodField()
    eventName = serializers.CharField(source="event.name", read_only=True)
    ticketType = serializers.CharField(source="ticket_type")
    registrationStatus = serializers.CharField(source="registration_status")
    paymentStatus = serializers.CharField(source="payment_status")
    ticketStatus = serializers.CharField(source="ticket_status")
    accessCode = serializers.CharField(source="access_code")
    status = serializers.CharField(source="check_in_status")
    registeredAt = serializers.SerializerMethodField()
    phone = serializers.CharField(source="attendee_phone")

    class Meta:
        model = Ticket
        fields = [
            "id",
            "name",
            "email",
            "avatar",
            "eventName",
            "ticketType",
            "registrationStatus",
            "paymentStatus",
            "ticketStatus",
            "accessCode",
            "status",
            "registeredAt",
            "phone",
        ]

    def get_avatar(self, obj):
        if obj.attendee_avatar:
            return obj.attendee_avatar.url
        return ""

    def get_registeredAt(self, obj):
        if obj.created_at:
            return obj.created_at.strftime("%d %B %Y")
        return ""


class MyTicketDetailSerializer(serializers.ModelSerializer):
    """
    Mobile My Event Ticket screen serializer (without seat_no)
    """
    event = EventSerializer(read_only=True)
    registration_id = serializers.CharField(source="ticket_id", read_only=True)
    venue = serializers.CharField(source="event.venue", read_only=True)
    date_display = serializers.SerializerMethodField()
    guidelines = serializers.SerializerMethodField()
    support_phone = serializers.SerializerMethodField()
    support_email = serializers.SerializerMethodField()
    is_free = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            "id",
            "ticket_id",
            "registration_id",
            "event",
            "attendee_name",
            "attendee_email",
            "ticket_type",
            "payment_status",
            "ticket_status",
            "registration_status",
            "check_in_status",
            "check_in_time_slot",
            "checked_in_at",
            "price",
            "price_amount",
            "is_free",
            "venue",
            "date_display",
            "qr_validation_token",
            "qr_code_data",
            "guidelines",
            "support_phone",
            "support_email",
        ]

    def get_is_free(self, obj):
        if obj.event:
            return obj.event.is_free
        return (obj.price_amount or 0) <= 0

    def get_date_display(self, obj):
        if obj.event:
            return f"{obj.event.start_date.strftime('%B %d')} – {obj.event.end_date.strftime('%B %d, %Y')}"
        return ""

    def get_guidelines(self, obj):
        return [
            "Bring a valid photo ID",
            "Have this QR Code ready",
            "Arrive at least 30 minutes early",
            "Follow event staff instructions",
        ]

    def get_support_phone(self, obj):
        return "1-800-REAL-SUCCESS"

    def get_support_email(self, obj):
        return "Support@realsuccess.com"
