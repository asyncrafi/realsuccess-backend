from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from apps.core.utils.mixins import BaseResponseMixin
from .models import TeamMember, Conversation
from .serializers import TeamMemberSerializer, ChatMessageSerializer, SendMessageRequestSerializer
from .consumers import (
    ensure_default_team_members,
    get_attendee_display_info,
    save_chat_message_sync,
    broadcast_chat_message_sync,
)


class TeamMemberListMessagesView(BaseResponseMixin, APIView):
    """
    Get list of team members with their conversations & messages.
    Supports both dashboard (?mode=admin or staff JWT) and mobile client.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        ensure_default_team_members()
        user = request.user if request.user.is_authenticated else None
        is_admin_mode = (
            (user and user.is_staff)
            or request.query_params.get("mode") == "admin"
        )

        if is_admin_mode:
            result = []

            # 1. Event Group Broadcast channels
            group_members = TeamMember.objects.filter(channel_type="event-group")
            for grp in group_members:
                conv, _ = Conversation.objects.get_or_create(
                    team_member=grp,
                    channel_type="event-group",
                    user=None,
                    defaults={"event": grp.event},
                )
                last_msg = conv.messages.last()
                result.append({
                    "id": str(grp.id),
                    "name": grp.name,
                    "displayName": grp.display_name,
                    "email": grp.email,
                    "avatar": grp.avatar or "/fallback_avatar.png",
                    "role": grp.role,
                    "online": grp.online,
                    "channelType": "event-group",
                    "eventName": grp.event.name if grp.event else None,
                    "lastMessage": last_msg.text if last_msg else "",
                    "lastMessageTime": last_msg.timestamp.strftime("%I:%M %p") if (last_msg and last_msg.timestamp) else "",
                    "unreadCount": conv.messages.filter(is_read=False, is_sender=False).count(),
                    "messages": ChatMessageSerializer(conv.messages.all(), many=True, context={"request": request}).data,
                })

            # 2. Attendee conversations (Direct Chat)
            conversations = (
                Conversation.objects.filter(channel_type="direct-staff")
                .select_related("user", "event", "team_member")
                .prefetch_related("messages")
                .order_by("-updated_at")
            )

            for conv in conversations:
                if not conv.user:
                    continue
                display_name, role, avatar = get_attendee_display_info(conv.user)
                last_msg = conv.messages.last()

                result.append({
                    "id": f"conv-{conv.id}",
                    "conversationId": str(conv.id),
                    "name": conv.user.email,
                    "displayName": display_name,
                    "email": conv.user.email,
                    "avatar": avatar,
                    "role": role,
                    "online": True,
                    "channelType": "direct-staff",
                    "eventName": conv.event.name if conv.event else None,
                    "lastMessage": last_msg.text if last_msg else "",
                    "lastMessageTime": last_msg.timestamp.strftime("%I:%M %p") if (last_msg and last_msg.timestamp) else "",
                    "unreadCount": conv.messages.filter(is_read=False, is_sender=False).count(),
                    "messages": ChatMessageSerializer(conv.messages.all(), many=True, context={"request": request}).data,
                })

            return self.success_response(data=result, message="Team conversations retrieved successfully")

        # For Mobile Attendee Client:
        members = TeamMember.objects.all().select_related("event").prefetch_related("conversations__messages")
        serializer = TeamMemberSerializer(members, many=True, context={"request": request})
        return self.success_response(
            data=serializer.data,
            message="Team members retrieved successfully",
        )


class SendChatMessageView(BaseResponseMixin, APIView):
    """
    Send a message to a team member, attendee conversation, or channel.
    Also broadcasts over WebSockets so both Admin Dashboard & Flutter update in real time.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SendMessageRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(
                message="Invalid payload",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        raw_member_id = str(serializer.validated_data["member_id"]).strip()
        text = serializer.validated_data["text"].strip()
        attachment_url = serializer.validated_data.get("attachment_url") or ""

        user = request.user if request.user.is_authenticated else None
        conv, new_msg = save_chat_message_sync(user, raw_member_id, text, attachment_url)

        # Broadcast real-time WebSocket event
        try:
            broadcast_chat_message_sync(conv, new_msg)
        except Exception as e:
            print(f"⚠️ [WS Broadcast Warning] {e}", flush=True)

        return self.success_response(
            data=ChatMessageSerializer(new_msg, context={"request": request}).data,
            message="Message sent successfully",
            status_code=status.HTTP_201_CREATED,
        )


class ConversationMessagesView(BaseResponseMixin, APIView):
    """
    Retrieve message history for a specific conversation.
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        conv = get_object_or_404(Conversation, pk=pk)
        messages = conv.messages.all()
        serializer = ChatMessageSerializer(messages, many=True, context={"request": request})
        return self.success_response(
            data=serializer.data,
            message="Messages retrieved successfully",
        )
