from rest_framework import serializers
from .models import Resource, UserResourceDownload


from apps.events.models import Event


class ResourceSerializer(serializers.ModelSerializer):
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all(), required=False, allow_null=True)
    eventName = serializers.CharField(source="event.name", read_only=True)
    fileSize = serializers.CharField(source="file_size", required=False, default="2.4 MB")
    fileUrl = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        model = Resource
        fields = [
            "id",
            "event",
            "eventName",
            "title",
            "description",
            "category",
            "type",
            "status",
            "file",
            "fileSize",
            "fileUrl",
            "is_featured",
            "download_count",
            "date",
            "created_at",
            "updated_at",
        ]

    def get_fileUrl(self, obj):
        if obj.file:
            return obj.file.url
        return obj.file_url

    def get_date(self, obj):
        if obj.created_at:
            return obj.created_at.strftime("%d %B %Y")
        return ""

    def create(self, validated_data):
        if not validated_data.get("event"):
            ev = Event.objects.first()
            if not ev:
                ev = Event.objects.create(name="RealSuccess Main Event", access_code="RS-MAIN-001")
            validated_data["event"] = ev
        if not validated_data.get("file_size"):
            validated_data["file_size"] = "2.4 MB"
        return super().create(validated_data)


class UserResourceDownloadSerializer(serializers.ModelSerializer):
    resource = ResourceSerializer(read_only=True)

    class Meta:
        model = UserResourceDownload
        fields = ["id", "resource", "downloaded_at"]
