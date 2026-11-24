from rest_framework import serializers
from .models import Event, EventStory


class EventStorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EventStory
        fields = ["id", "title", "video_url", "thumbnail", "duration", "order", "created_at"]


class EventSerializer(serializers.ModelSerializer):
    attendees = serializers.IntegerField(source="attendees_count", read_only=True)
    tickets = serializers.IntegerField(source="total_tickets", read_only=True)
    date = serializers.SerializerMethodField()

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
            "status",
            "banner_image",
            "qr_code_url",
            "created_at",
            "updated_at",
        ]

    def get_date(self, obj):
        if obj.start_date:
            return obj.start_date.strftime("%d %B %Y")
        return ""


class EventDetailSerializer(EventSerializer):
    stories = EventStorySerializer(many=True, read_only=True)
    confirmed_registrations = serializers.IntegerField(read_only=True)

    class Meta(EventSerializer.Meta):
        fields = EventSerializer.Meta.fields + ["stories", "confirmed_registrations"]


class VerifyAccessCodeSerializer(serializers.Serializer):
    access_code = serializers.CharField(required=True)
