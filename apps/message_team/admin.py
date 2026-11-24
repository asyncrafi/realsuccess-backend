from django.contrib import admin
from .models import TeamMember, Conversation, ChatMessage


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ["timestamp"]


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ["displayName", "name", "email", "role", "online", "channel_type", "event"]
    list_filter = ["online", "channel_type", "role", "event"]
    search_fields = ["name", "display_name", "email"]

    def displayName(self, obj):
        return obj.display_name


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "team_member", "user", "channel_type", "event", "created_at"]
    list_filter = ["channel_type", "event"]
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ["id", "conversation", "sender_name", "is_sender", "timestamp", "is_read"]
    list_filter = ["is_sender", "is_read", "timestamp"]
    search_fields = ["sender_name", "text"]
