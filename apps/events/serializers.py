import uuid
from decimal import Decimal
from django.utils import timezone
from rest_framework import serializers
from .models import Event, EventStory


class EventStorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EventStory
        fields = ["id", "title", "video_url", "thumbnail", "duration", "order", "created_at"]


class EventSerializer(serializers.ModelSerializer):
    attendees = serializers.IntegerField(source="attendees_count", read_only=True)
    tickets = serializers.IntegerField(source="total_tickets", required=False)
    date = serializers.SerializerMethodField()
    start_date = serializers.DateField(required=False, default=timezone.localdate)
    end_date = serializers.DateField(required=False, default=timezone.localdate)
    access_code = serializers.CharField(required=False)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=Decimal("0.00"))
    is_free = serializers.BooleanField(read_only=True)
    price_display = serializers.SerializerMethodField()
    qr_registration_token = serializers.CharField(read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "name",
            "description",
            "access_code",
            "venue",
            "date",
            "start_date",
            "end_date",
            "days_duration",
            "total_tickets",
            "tickets",
            "attendees",
            "price",
            "is_free",
            "price_display",
            "status",
            "banner_image",
            "qr_registration_token",
            "qr_code_url",
            "created_at",
            "updated_at",
        ]

    def get_date(self, obj):
        if obj.start_date:
            return obj.start_date.strftime("%d %B %Y")
        return ""

    def get_price_display(self, obj):
        if obj.is_free:
            return "Free"
        return f"${obj.price:,.2f}"

    def validate_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Event price cannot be negative.")
        return value

    def create(self, validated_data):
        if not validated_data.get("access_code"):
            validated_data["access_code"] = f"RS-{uuid.uuid4().hex[:6].upper()}"
        if not validated_data.get("start_date"):
            validated_data["start_date"] = timezone.localdate()
        if not validated_data.get("end_date"):
            validated_data["end_date"] = timezone.localdate()
        if not validated_data.get("total_tickets"):
            validated_data["total_tickets"] = 400
        return super().create(validated_data)


class EventDetailSerializer(EventSerializer):
    stories = EventStorySerializer(many=True, read_only=True)
    confirmed_registrations = serializers.IntegerField(read_only=True)

    class Meta(EventSerializer.Meta):
        fields = EventSerializer.Meta.fields + ["stories", "confirmed_registrations"]


class VerifyAccessCodeSerializer(serializers.Serializer):
    access_code = serializers.CharField(required=True)


class EventQRRegisterSerializer(serializers.Serializer):
    qr_registration_token = serializers.CharField(required=False, allow_blank=True)
    event_id = serializers.IntegerField(required=False)
    access_code = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    ticket_type = serializers.ChoiceField(choices=["VIP", "General", "Executive"], required=False, default="General")
