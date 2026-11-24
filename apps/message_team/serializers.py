from rest_framework import serializers
from .models import TeamMember, Conversation, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    senderId = serializers.SerializerMethodField()
    senderName = serializers.CharField(source="sender_name")
    isSender = serializers.BooleanField(source="is_sender")
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

    def get_timestamp(self, obj):
        return obj.timestamp.strftime("%I:%M %p") if obj.timestamp else ""


class TeamMemberSerializer(serializers.ModelSerializer):
    displayName = serializers.CharField(source="display_name")
    channelType = serializers.CharField(source="channel_type")
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
            return ChatMessageSerializer(conv.messages.all(), many=True).data
        return []


class SendMessageRequestSerializer(serializers.Serializer):
    member_id = serializers.CharField(required=True)
    text = serializers.CharField(required=True)
    attachment_url = serializers.URLField(required=False, allow_blank=True)
