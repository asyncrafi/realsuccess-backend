from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from apps.core.utils.mixins import BaseResponseMixin
from .models import TeamMember, Conversation, ChatMessage
from .serializers import TeamMemberSerializer, ChatMessageSerializer, SendMessageRequestSerializer


class TeamMemberListMessagesView(BaseResponseMixin, APIView):
    """
    Get list of team members with their conversations & messages.
    Supports both dashboard and mobile client.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        members = TeamMember.objects.all().select_related("event").prefetch_related("conversations__messages")
        serializer = TeamMemberSerializer(members, many=True, context={"request": request})
        return self.success_response(
            data=serializer.data,
            message="Team members retrieved successfully"
        )


class SendChatMessageView(BaseResponseMixin, APIView):
    """
    Send a message to a team member or channel.
    Accepts: { "member_id": "<id>", "text": "message text", "attachment_url": "" }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SendMessageRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(
                message="Invalid payload",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        member_id = serializer.validated_data["member_id"]
        text = serializer.validated_data["text"]
        attachment_url = serializer.validated_data.get("attachment_url")

        # Find team member
        try:
            member = TeamMember.objects.get(id=member_id)
        except (TeamMember.DoesNotExist, ValueError):
            member = TeamMember.objects.first()
            if not member:
                return self.error_response(message="Team member not found", status_code=status.HTTP_404_NOT_FOUND)

        user = request.user if request.user.is_authenticated else None
        is_sender = user.is_staff if user else False
        sender_name = user.get_full_name() or user.email if user else "Attendee"
        if is_sender and user:
            sender_name = user.get_full_name() or "Admin"

        # Find or create conversation
        conv = Conversation.objects.filter(team_member=member, user=user).first()
        if not conv:
            conv = Conversation.objects.create(
                team_member=member,
                user=user,
                channel_type=member.channel_type,
                event=member.event
            )

        new_msg = ChatMessage.objects.create(
            conversation=conv,
            sender_user=user if not is_sender else None,
            sender_staff=member if is_sender else None,
            sender_name=sender_name,
            text=text,
            is_sender=is_sender,
            attachment_url=attachment_url
        )

        return self.success_response(
            data=ChatMessageSerializer(new_msg).data,
            message="Message sent successfully",
            status_code=status.HTTP_201_CREATED
        )


class ConversationMessagesView(BaseResponseMixin, APIView):
    """
    Retrieve message history for a specific conversation.
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        conv = get_object_or_404(Conversation, pk=pk)
        messages = conv.messages.all()
        serializer = ChatMessageSerializer(messages, many=True)
        return self.success_response(
            data=serializer.data,
            message="Messages retrieved successfully"
        )
