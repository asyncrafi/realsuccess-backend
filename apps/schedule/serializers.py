from rest_framework import serializers
from .models import Speaker, Session, SessionResource, SessionBookmark


class SessionResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionResource
        fields = ["id", "title", "file", "file_size", "file_type", "created_at"]


class SpeakerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Speaker
        fields = [
            "id",
            "name",
            "role",
            "organization",
            "avatar",
            "bio",
            "years_of_experience",
            "workshops_conducted",
            "specialization",
            "industry",
            "areas_of_expertise",
            "official_website",
            "company_name",
            "is_keynote_spotlight",
        ]


class SessionListSerializer(serializers.ModelSerializer):
    speakerName = serializers.CharField(source="speaker.name", read_only=True, default="")
    speakerRole = serializers.CharField(source="speaker.role", read_only=True, default="")
    sessionTitle = serializers.CharField(source="session_title")
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = [
            "id",
            "event",
            "day_number",
            "date",
            "sessionTitle",
            "time",
            "start_time",
            "end_time",
            "venue",
            "duration",
            "type",
            "status",
            "speaker",
            "speakerName",
            "speakerRole",
            "description",
            "is_bookmarked",
            "order",
        ]

    def get_is_bookmarked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.bookmarks.filter(user=request.user).exists()
        return False


class SessionDetailSerializer(SessionListSerializer):
    speaker = SpeakerSerializer(read_only=True)
    speaker_id = serializers.PrimaryKeyRelatedField(
        source="speaker",
        queryset=Speaker.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )
    resources = SessionResourceSerializer(many=True, read_only=True)
    related_sessions = serializers.SerializerMethodField()

    class Meta(SessionListSerializer.Meta):
        fields = SessionListSerializer.Meta.fields + [
            "speaker_id",
            "important_notes",
            "resources",
            "related_sessions",
        ]

    def get_related_sessions(self, obj):
        related = Session.objects.filter(
            event=obj.event,
            status="Published"
        ).exclude(id=obj.id)[:3]
        return SessionListSerializer(related, many=True, context=self.context).data


class SpeakerDetailSerializer(SpeakerSerializer):
    sessions = SessionListSerializer(many=True, read_only=True)

    class Meta(SpeakerSerializer.Meta):
        fields = SpeakerSerializer.Meta.fields + ["sessions"]
