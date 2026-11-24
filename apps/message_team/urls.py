from django.urls import path
from .views import TeamMemberListMessagesView, SendChatMessageView, ConversationMessagesView

app_name = "message_team"

urlpatterns = [
    path("team/", TeamMemberListMessagesView.as_view(), name="team-list"),
    path("messages/", SendChatMessageView.as_view(), name="send-message"),
    path("conversations/<uuid:pk>/messages/", ConversationMessagesView.as_view(), name="conversation-messages"),
]
