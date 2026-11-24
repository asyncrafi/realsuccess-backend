import uuid
from django.db import models
from django.conf import settings
from apps.events.models import Event


class TeamMember(models.Model):
    CHANNEL_CHOICES = (
        ("event-group", "Event Group"),
        ("direct-staff", "Direct Staff"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="team_profiles"
    )
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, help_text="e.g. Elena R.")
    email = models.EmailField()
    avatar = models.URLField(max_length=500, blank=True, null=True)
    role = models.CharField(max_length=150, default="Event Coordinator")
    online = models.BooleanField(default=True)
    channel_type = models.CharField(max_length=50, choices=CHANNEL_CHOICES, default="direct-staff")
    event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="team_members"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Team Member"
        verbose_name_plural = "Team Members"

    def __str__(self):
        return f"{self.display_name} ({self.role})"


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team_member = models.ForeignKey(
        TeamMember,
        on_delete=models.CASCADE,
        related_name="conversations"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_conversations",
        null=True,
        blank=True
    )
    channel_type = models.CharField(
        max_length=50,
        choices=TeamMember.CHANNEL_CHOICES,
        default="direct-staff"
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversations"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Chat with {self.team_member.display_name}"


class ChatMessage(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    sender_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    sender_staff = models.ForeignKey(
        TeamMember,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    sender_name = models.CharField(max_length=255)
    text = models.TextField()
    is_sender = models.BooleanField(
        default=False,
        help_text="True if sent by RealSuccess Staff / Admin"
    )
    attachment_url = models.URLField(max_length=500, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.sender_name}: {self.text[:30]}"
