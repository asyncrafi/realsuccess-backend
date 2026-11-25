from rest_framework import serializers
from .models import TeamMember, Conversation, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    senderId = serializers.SerializerMethodField()
    senderName = serializers.SerializerMethodField()
    isSender = serializers.SerializerMethodField()
    timestamp = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "senderId",
            "senderName",
            "text",
            "timestamp",
            "isSender",
            "attachment_url",
            "is_read",
        ]

    def get_senderId(self, obj):
        if obj.sender_staff:
            return str(obj.sender_staff.id)
        if obj.sender_user:
            return str(obj.sender_user.id)
        return "admin" if obj.is_sender else "user"

    def get_senderName(self, obj):
        if obj.sender_name and obj.sender_name != "Attendee":
            return obj.sender_name
        if not obj.is_sender and obj.conversation and obj.conversation.user:
            from .consumers import get_attendee_display_info
            display_name, _, _ = get_attendee_display_info(obj.conversation.user)
            return display_name
        return obj.sender_name or "Attendee"

    def get_isSender(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if request.user.is_staff:
                return bool(obj.is_sender or obj.sender_user == request.user)
            else:
                return bool(obj.sender_user == request.user and not obj.is_sender)
        return bool(obj.is_sender)

    def get_timestamp(self, obj):
        return obj.timestamp.strftime("%I:%M %p") if obj.timestamp else ""


class TeamMemberSerializer(serializers.ModelSerializer):
    displayName = serializers.CharField(source="display_name")
    channelType = serializers.CharField(source="channel_type")
    avatar = serializers.SerializerMethodField()
    eventName = serializers.SerializerMethodField()
    lastMessage = serializers.SerializerMethodField()
    lastMessageTime = serializers.SerializerMethodField()
    unreadCount = serializers.SerializerMethodField()
    messages = serializers.SerializerMethodField()

    class Meta:
        model = TeamMember
        fields = [
            "id",
            "name",
            "displayName",
            "email",
            "avatar",
            "role",
            "online",
            "channelType",
            "eventName",
            "lastMessage",
            "lastMessageTime",
            "unreadCount",
            "messages",
        ]

    def get_avatar(self, obj):
        return obj.avatar or "/fallback_avatar.png"

    def get_eventName(self, obj):
        return obj.event.name if obj.event else None

    def _get_conversation(self, obj):
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None
        conv = obj.conversations.first()
        if user and not user.is_staff:
            user_conv = obj.conversations.filter(user=user).first()
            if user_conv:
                return user_conv
        return conv

    def get_lastMessage(self, obj):
        conv = self._get_conversation(obj)
        if conv:
            last_msg = conv.messages.last()
            return last_msg.text if last_msg else ""
        return ""

    def get_lastMessageTime(self, obj):
        conv = self._get_conversation(obj)
        if conv:
            last_msg = conv.messages.last()
            return last_msg.timestamp.strftime("%I:%M %p") if (last_msg and last_msg.timestamp) else ""
        return ""

    def get_unreadCount(self, obj):
        conv = self._get_conversation(obj)
        if conv:
            return conv.messages.filter(is_read=False).count()
        return 0

    def get_messages(self, obj):
        conv = self._get_conversation(obj)
        if conv:
            return ChatMessageSerializer(conv.messages.all(), many=True, context=self.context).data
        return []


class SendMessageRequestSerializer(serializers.Serializer):
    member_id = serializers.CharField(required=True)
    text = serializers.CharField(required=False, allow_blank=True, default="")
    attachment_url = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if not (attrs.get("text") or "").strip() and not (attrs.get("attachment_url") or "").strip():
            raise serializers.ValidationError("Either text or attachment_url is required.")
        return attrs
