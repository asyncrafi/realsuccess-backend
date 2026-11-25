import os
import uuid
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
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

            # Attendee direct conversations sorted by most recent message
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
                last_msg_text = ""
                if last_msg:
                    last_msg_text = last_msg.text or ("📎 Attachment" if last_msg.attachment_url else "")

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
                    "lastMessage": last_msg_text,
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
        text = (serializer.validated_data.get("text") or "").strip()
        attachment_url = (serializer.validated_data.get("attachment_url") or "").strip()

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


class ChatAttachmentUploadView(BaseResponseMixin, APIView):
    """
    Uploads a chat attachment (image, PDF, doc, etc.) and returns its public URL.
    """
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file") or request.FILES.get("attachment")
        if not uploaded_file:
            return self.error_response(
                message="No file provided. Send multipart form-data with key 'file'.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        ext = os.path.splitext(uploaded_file.name)[1]
        safe_name = f"chat_attachments/{uuid.uuid4().hex}{ext}"
        saved_path = default_storage.save(safe_name, ContentFile(uploaded_file.read()))
        relative_url = f"{settings.MEDIA_URL}{saved_path}"

        # Build absolute HTTPS URL
        scheme = "https" if not settings.DEBUG or request.is_secure() or request.META.get("HTTP_X_FORWARDED_PROTO") == "https" else request.scheme
        host = request.get_host()
        full_url = f"{scheme}://{host}{relative_url}" if host else relative_url

        return self.success_response(
            data={
                "url": full_url,
                "relative_url": relative_url,
                "filename": uploaded_file.name,
                "size": uploaded_file.size,
                "content_type": uploaded_file.content_type,
            },
            message="Attachment uploaded successfully",
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
