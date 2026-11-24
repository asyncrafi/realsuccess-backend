from rest_framework import serializers
from .models import Announcement, AnnouncementAttachment


class AnnouncementAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnouncementAttachment
        fields = ["id", "name", "file", "file_type", "size", "created_at"]


class AnnouncementSerializer(serializers.ModelSerializer):
    eventName = serializers.CharField(source="event.name", read_only=True)
    publishedBy = serializers.CharField(source="published_by")
    date = serializers.SerializerMethodField()
    attachments = AnnouncementAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Announcement
        fields = [
            "id",
            "event",
            "eventName",
            "title",
            "category",
            "priority",
            "status",
            "content",
            "takeaway_time",
            "takeaway_venue",
            "publishedBy",
            "reading_time",
            "is_new",
            "date",
            "attachments",
            "created_at",
            "updated_at",
        ]

    def get_date(self, obj):
        if obj.created_at:
            return obj.created_at.strftime("%d %B %Y")
        return ""


class AnnouncementDetailSerializer(AnnouncementSerializer):
    related_announcements = serializers.SerializerMethodField()

    class Meta(AnnouncementSerializer.Meta):
        fields = AnnouncementSerializer.Meta.fields + ["related_announcements"]

    def get_related_announcements(self, obj):
        related = Announcement.objects.filter(
            event=obj.event,
            status="Published"
        ).exclude(id=obj.id)[:3]
        return AnnouncementSerializer(related, many=True).data
