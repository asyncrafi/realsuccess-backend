import json
import uuid
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from .models import TeamMember, Conversation, ChatMessage


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
        },
    )
    TeamMember.objects.get_or_create(
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
        },
    )
    return member1


def get_attendee_display_info(user):
    """Returns (display_name, role, avatar) for an attendee user."""
    if not user:
        return "Attendee", "Attendee", "/fallback_avatar.png"

    from apps.tickets.models import Ticket

    ticket = Ticket.objects.filter(user=user).first()
    if not ticket and user.email:
        ticket = Ticket.objects.filter(attendee_email__iexact=user.email).first()

    profile_name = ""
    if hasattr(user, "profile") and user.profile and getattr(user.profile, "name", None):
        profile_name = user.profile.name

    display_name = (
        (ticket.attendee_name if ticket and ticket.attendee_name else None)
        or profile_name
        or user.get_full_name()
        or (user.email.split("@")[0].capitalize() if user.email else "Attendee")
    )
    role = f"Attendee ({ticket.ticket_type} Pass)" if ticket else "Attendee"
    avatar = (
        ticket.attendee_avatar.url
        if (ticket and ticket.attendee_avatar)
        else "/fallback_avatar.png"
    )
    return display_name, role, avatar


def build_ws_payload(conv, msg):
    display_name, role, avatar = get_attendee_display_info(conv.user)
    sender_id = (
        str(msg.sender_staff.id)
        if msg.sender_staff
        else (str(msg.sender_user.id) if msg.sender_user else ("admin" if msg.is_sender else "user"))
    )
    return {
        "type": "chat_message_event",
        "conversation_id": str(conv.id),
        "member_id": str(conv.team_member.id),
        "channel_type": conv.channel_type,
        "sender_user_id": msg.sender_user.id if msg.sender_user else None,
        "attendee_id": f"conv-{conv.id}",
        "attendee_display_name": display_name,
        "attendee_email": conv.user.email if conv.user else "",
        "attendee_role": role,
        "attendee_avatar": avatar,
        "event_name": conv.event.name if conv.event else None,
        "is_staff": bool(msg.is_sender),
        "message": {
            "id": msg.id,
            "senderId": sender_id,
            "senderName": msg.sender_name,
            "text": msg.text,
            "timestamp": msg.timestamp.strftime("%I:%M %p") if msg.timestamp else "",
            "isSender": bool(msg.is_sender),
            "isStaff": bool(msg.is_sender),
            "attachment_url": msg.attachment_url or "",
            "is_read": msg.is_read,
        },
    }


def broadcast_chat_message_sync(conv, msg):
    """Broadcasts a newly saved ChatMessage to admin + target user/group via Redis channel layer."""
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    payload = build_ws_payload(conv, msg)

    # Always notify admin dashboard group
    async_to_sync(channel_layer.group_send)("chat_admin", payload)

    if conv.channel_type == "event-group":
        async_to_sync(channel_layer.group_send)("chat_event_group", payload)
    elif conv.user:
        async_to_sync(channel_layer.group_send)(f"chat_user_{conv.user.id}", payload)


def save_chat_message_sync(user, raw_member_id, text, attachment_url=""):
    """Resolves conversation, saves ChatMessage, and returns (conv, new_msg)."""
    ensure_default_team_members()
    is_staff = bool(user and user.is_authenticated and user.is_staff)
    auth_user = user if (user and user.is_authenticated) else None

    conv = None
    clean_uuid = str(raw_member_id).strip().replace("conv-", "")
    try:
        uuid_obj = uuid.UUID(clean_uuid)
        conv = Conversation.objects.select_related("user", "team_member", "event").filter(id=uuid_obj).first()
    except ValueError:
        pass

    if not conv:
        member = None
        try:
            member = TeamMember.objects.filter(id=int(raw_member_id)).first()
        except (ValueError, TypeError):
            pass

        if not member:
            member = TeamMember.objects.first() or ensure_default_team_members()

        if is_staff:
            if member.channel_type == "event-group":
                conv, _ = Conversation.objects.get_or_create(
                    team_member=member,
                    channel_type="event-group",
                    user=None,
                    defaults={"event": member.event},
                )
            else:
                conv = Conversation.objects.filter(team_member=member).order_by("-updated_at").first()
                if not conv:
                    conv = Conversation.objects.create(
                        team_member=member,
                        channel_type="direct-staff",
                        event=member.event,
                    )
        else:
            conv, _ = Conversation.objects.get_or_create(
                team_member=member,
                user=auth_user,
                defaults={
                    "channel_type": member.channel_type,
                    "event": member.event,
                },
            )

    if is_staff:
        sender_name = "RealSuccess Staff"
    else:
        display_name, _, _ = get_attendee_display_info(auth_user)
        sender_name = display_name

    new_msg = ChatMessage.objects.create(
        conversation=conv,
        sender_user=auth_user if not is_staff else None,
        sender_staff=conv.team_member if is_staff else None,
        sender_name=sender_name,
        text=text.strip(),
        is_sender=is_staff,
        attachment_url=attachment_url or "",
    )

    conv.updated_at = timezone.now()
    conv.save(update_fields=["updated_at"])
    return conv, new_msg


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        self.groups_joined = []

        if self.user and self.user.is_authenticated:
            if self.user.is_staff:
                await self.channel_layer.group_add("chat_admin", self.channel_name)
                self.groups_joined.append("chat_admin")
            else:
                user_group = f"chat_user_{self.user.id}"
                await self.channel_layer.group_add(user_group, self.channel_name)
                await self.channel_layer.group_add("chat_event_group", self.channel_name)
                self.groups_joined.extend([user_group, "chat_event_group"])
        else:
            await self.channel_layer.group_add("chat_event_group", self.channel_name)
            self.groups_joined.append("chat_event_group")

        await self.accept()
        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "authenticated": bool(self.user and self.user.is_authenticated),
            "is_staff": bool(self.user and self.user.is_authenticated and self.user.is_staff),
            "user_id": self.user.id if (self.user and self.user.is_authenticated) else None,
        }))

    async def disconnect(self, close_code):
        for group_name in self.groups_joined:
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"type": "error", "message": "Invalid JSON"}))
            return

        msg_type = data.get("type", "chat_message")
        if msg_type == "ping":
            await self.send(text_data=json.dumps({"type": "pong"}))
            return

        if msg_type in ("chat_message", "send_message"):
            text = (data.get("text") or "").strip()
            member_id = data.get("member_id") or data.get("conversation_id") or "1"
            attachment_url = data.get("attachment_url") or ""

            if not text:
                await self.send(text_data=json.dumps({"type": "error", "message": "Message text is required"}))
                return

            conv, new_msg = await database_sync_to_async(save_chat_message_sync)(
                self.user, member_id, text, attachment_url
            )
            payload = await database_sync_to_async(build_ws_payload)(conv, new_msg)

            await self.channel_layer.group_send("chat_admin", payload)
            if conv.channel_type == "event-group":
                await self.channel_layer.group_send("chat_event_group", payload)
            elif conv.user:
                await self.channel_layer.group_send(f"chat_user_{conv.user.id}", payload)

    async def chat_message_event(self, event):
        """Forwards broadcast message to WebSocket client with per-recipient isSender flag."""
        msg_data = dict(event["message"])
        is_staff_msg = event.get("is_staff", False)
        sender_user_id = event.get("sender_user_id")

        if self.user and self.user.is_authenticated and self.user.is_staff:
            msg_data["isSender"] = bool(is_staff_msg)
        elif self.user and self.user.is_authenticated:
            msg_data["isSender"] = bool(not is_staff_msg and sender_user_id == self.user.id)
        else:
            msg_data["isSender"] = bool(is_staff_msg)

        out = {
            "type": "new_message",
            "conversation_id": event["conversation_id"],
            "member_id": event["member_id"],
            "channel_type": event["channel_type"],
            "attendee_id": event["attendee_id"],
            "attendee_display_name": event["attendee_display_name"],
            "attendee_email": event["attendee_email"],
            "attendee_role": event["attendee_role"],
            "attendee_avatar": event["attendee_avatar"],
            "event_name": event["event_name"],
            "message": msg_data,
        }
        await self.send(text_data=json.dumps(out))
