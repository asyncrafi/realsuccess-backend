from rest_framework import serializers
from .models import Ticket
from apps.events.serializers import EventSerializer


class TicketSerializer(serializers.ModelSerializer):
    eventName = serializers.CharField(source="event.name", read_only=True)
    attendeeName = serializers.CharField(source="attendee_name")
    attendeeEmail = serializers.EmailField(source="attendee_email")
    attendeePhone = serializers.CharField(source="attendee_phone", required=False)
    ticketType = serializers.CharField(source="ticket_type")
    checkInStatus = serializers.CharField(source="check_in_status")
    issueDate = serializers.SerializerMethodField()
    status = serializers.CharField(source="registration_status")

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
            "checkInStatus",
            "check_in_time_slot",
            "checked_in_at",
            "access_code",
            "qr_code_data",
            "price",
            "seat_no",
            "issueDate",
            "status",
            "created_at",
        ]

    ticketId = serializers.CharField(source="ticket_id", read_only=True)

    def get_issueDate(self, obj):
        if obj.issue_date:
            return obj.issue_date.strftime("%d %B %Y")
        return ""


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
    Mobile My Event Ticket screen serializer matching ticket.png
    """
    event = EventSerializer(read_only=True)
    registration_id = serializers.CharField(source="ticket_id", read_only=True)
    venue = serializers.CharField(source="event.venue", read_only=True)
    date_display = serializers.SerializerMethodField()
    guidelines = serializers.SerializerMethodField()
    support_phone = serializers.SerializerMethodField()
    support_email = serializers.SerializerMethodField()

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
            "registration_status",
            "check_in_status",
            "check_in_time_slot",
            "checked_in_at",
            "venue",
            "date_display",
            "qr_code_data",
            "guidelines",
            "support_phone",
            "support_email",
        ]

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
