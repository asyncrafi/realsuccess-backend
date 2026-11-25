import uuid
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from apps.core.utils.mixins import BaseResponseMixin
from .models import TeamMember, Conversation, ChatMessage
from .serializers import TeamMemberSerializer, ChatMessageSerializer, SendMessageRequestSerializer


def ensure_default_team_members():
    from apps.events.models import Event
    event = Event.objects.filter(status="Active").first() or Event.objects.first()

    member1, _ = TeamMember.objects.get_or_create(
        id=1,
        defaults={
            "name": "RealSuccess Support",
            "display_name": "Event Support Team",
            "email": "support@ourrealsuccess.com",
            "role": "Event Coordinator",
            "online": True,
            "channel_type": "direct-staff",
            "event": event,
            "avatar": "/fallback_avatar.png",
        }
    )
    member2, _ = TeamMember.objects.get_or_create(
        id=2,
        defaults={
            "name": "Event Group Broadcast",
            "display_name": "Group: Event Broadcast",
            "email": "broadcast@ourrealsuccess.com",
            "role": "Private Event Group (Staff Broadcast)",
            "online": True,
            "channel_type": "event-group",
            "event": event,
            "avatar": "/fallback_avatar.png",
        }
    )
    return member1


class TeamMemberListMessagesView(BaseResponseMixin, APIView):
    """
    Get list of team members with their conversations & messages.
    Supports both dashboard and mobile client.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        ensure_default_team_members()
        user = request.user if request.user.is_authenticated else None
        is_staff = user.is_staff if user else False

        if is_staff:
            from apps.tickets.models import Ticket
            result = []

            # 1. Event Group Broadcast channels
            group_members = TeamMember.objects.filter(channel_type="event-group")
            for grp in group_members:
                conv, _ = Conversation.objects.get_or_create(
                    team_member=grp,
                    channel_type="event-group",
                    user=None,
                    defaults={"event": grp.event}
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

            seen_conv_ids = set()
            for conv in conversations:
                if not conv.user:
                    continue
                seen_conv_ids.add(conv.id)
                ticket = Ticket.objects.filter(user=conv.user).first()
                if not ticket and conv.user.email:
                    ticket = Ticket.objects.filter(attendee_email__iexact=conv.user.email).first()

                display_name = (
                    ticket.attendee_name
                    if ticket and ticket.attendee_name
                    else (conv.user.get_full_name() or conv.user.email.split("@")[0].capitalize())
                )
                role = f"Attendee ({ticket.ticket_type} Pass)" if ticket else "Attendee"
                avatar = (
                    ticket.attendee_avatar.url
                    if (ticket and ticket.attendee_avatar)
                    else (conv.team_member.avatar or "/fallback_avatar.png")
                )
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

            # If no attendee has messaged yet, also include staff member entry so list is never empty
            if len(result) == 0:
                members = TeamMember.objects.all().select_related("event").prefetch_related("conversations__messages")
                serializer = TeamMemberSerializer(members, many=True, context={"request": request})
                return self.success_response(data=serializer.data, message="Team members retrieved successfully")

            return self.success_response(data=result, message="Team conversations retrieved successfully")

        # For Mobile Attendee Client:
        members = TeamMember.objects.all().select_related("event").prefetch_related("conversations__messages")
        serializer = TeamMemberSerializer(members, many=True, context={"request": request})
        return self.success_response(
            data=serializer.data,
            message="Team members retrieved successfully"
        )


class SendChatMessageView(BaseResponseMixin, APIView):
    """
    Send a message to a team member, attendee conversation, or channel.
    Accepts: { "member_id": "<id>", "text": "message text", "attachment_url": "" }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        ensure_default_team_members()
        serializer = SendMessageRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(
                message="Invalid payload",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        raw_member_id = str(serializer.validated_data["member_id"]).strip()
        text = serializer.validated_data["text"].strip()
        attachment_url = serializer.validated_data.get("attachment_url") or ""

        user = request.user if request.user.is_authenticated else None
        is_staff = user.is_staff if user else False

        conv = None

        # 1. Check if raw_member_id is a Conversation ID (e.g. conv-<uuid> or <uuid>)
        clean_uuid = raw_member_id.replace("conv-", "")
        try:
            uuid_obj = uuid.UUID(clean_uuid)
            conv = Conversation.objects.filter(id=uuid_obj).first()
        except ValueError:
            pass

        # 2. Check if raw_member_id is a TeamMember ID
        if not conv:
            member = None
            try:
                member = TeamMember.objects.filter(id=int(raw_member_id)).first()
            except ValueError:
                pass

            if not member:
                member = TeamMember.objects.first() or ensure_default_team_members()

            if is_staff:
                # Staff sending to channel or latest conversation
                if member.channel_type == "event-group":
                    conv, _ = Conversation.objects.get_or_create(
                        team_member=member,
                        channel_type="event-group",
                        user=None,
                        defaults={"event": member.event}
                    )
                else:
                    conv = Conversation.objects.filter(team_member=member).order_by("-updated_at").first()
                    if not conv:
                        conv = Conversation.objects.create(
                            team_member=member,
                            channel_type="direct-staff",
                            event=member.event
                        )
            else:
                # Attendee sending from mobile app
                conv, _ = Conversation.objects.get_or_create(
                    team_member=member,
                    user=user,
                    defaults={
                        "channel_type": member.channel_type,
                        "event": member.event
                    }
                )

        is_sender = is_staff
        sender_name = "RealSuccess Staff" if is_staff else (user.get_full_name() or user.email if user else "Attendee")

        new_msg = ChatMessage.objects.create(
            conversation=conv,
            sender_user=user if not is_staff else None,
            sender_staff=conv.team_member if is_staff else None,
            sender_name=sender_name,
            text=text,
            is_sender=is_sender,
            attachment_url=attachment_url
        )

        conv.updated_at = timezone.now()
        conv.save(update_fields=["updated_at"])

        return self.success_response(
            data=ChatMessageSerializer(new_msg, context={"request": request}).data,
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
        serializer = ChatMessageSerializer(messages, many=True, context={"request": request})
        return self.success_response(
            data=serializer.data,
            message="Messages retrieved successfully"
        )
