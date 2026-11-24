from rest_framework import serializers
from .models import Resource, UserResourceDownload


class ResourceSerializer(serializers.ModelSerializer):
    eventName = serializers.CharField(source="event.name", read_only=True)
    fileSize = serializers.CharField(source="file_size")
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


class UserResourceDownloadSerializer(serializers.ModelSerializer):
    resource = ResourceSerializer(read_only=True)

    class Meta:
        model = UserResourceDownload
        fields = ["id", "resource", "downloaded_at"]
