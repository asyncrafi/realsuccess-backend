from django.utils import timezone
from rest_framework import serializers
from .models import Speaker, Session, SessionResource, SessionBookmark
from apps.events.models import Event


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
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all(), required=False, allow_null=True)
    event_name = serializers.CharField(source="event.name", read_only=True)
    date = serializers.DateField(required=False)
    time = serializers.CharField(required=False, default="09:00 AM – 10:30 AM")
    venue = serializers.CharField(required=False, default="Main Hall")
    speakerName = serializers.CharField(required=False, allow_blank=True, default="")
    speakerRole = serializers.CharField(required=False, allow_blank=True, default="")
    sessionTitle = serializers.CharField(source="session_title")
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = [
            "id",
            "event",
            "event_name",
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

    def to_representation(self, obj):
        data = super().to_representation(obj)
        if obj.speaker:
            data["speakerName"] = obj.speaker.name
            data["speakerRole"] = obj.speaker.role
        return data

    def create(self, validated_data):
        speaker_name = validated_data.pop("speakerName", "")
        speaker_role = validated_data.pop("speakerRole", "")
        if not validated_data.get("event"):
            ev = Event.objects.first()
            if not ev:
                ev = Event.objects.create(name="RealSuccess Main Event", access_code="RS-MAIN-001")
            validated_data["event"] = ev
        if not validated_data.get("date"):
            validated_data["date"] = timezone.localdate()
        ev = validated_data.get("event")
        if ev and ev.start_date and validated_data.get("date"):
            validated_data["day_number"] = max(1, (validated_data["date"] - ev.start_date).days + 1)
        if speaker_name and not validated_data.get("speaker"):
            speaker, _ = Speaker.objects.get_or_create(
                name=speaker_name,
                defaults={"role": speaker_role or "Keynote Speaker"}
            )
            validated_data["speaker"] = speaker
        return super().create(validated_data)

    def update(self, instance, validated_data):
        speaker_name = validated_data.pop("speakerName", None)
        speaker_role = validated_data.pop("speakerRole", None)
        ev = validated_data.get("event", instance.event)
        dt = validated_data.get("date", instance.date)
        if ev and ev.start_date and dt:
            validated_data["day_number"] = max(1, (dt - ev.start_date).days + 1)
        if speaker_name:
            speaker, _ = Speaker.objects.get_or_create(
                name=speaker_name,
                defaults={"role": speaker_role or "Keynote Speaker"}
            )
            if speaker_role and speaker.role != speaker_role:
                speaker.role = speaker_role
                speaker.save(update_fields=["role"])
            validated_data["speaker"] = speaker
        return super().update(instance, validated_data)


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
