from django.urls import path
from . import views

urlpatterns = [
    path("send/", views.SendMessageView.as_view(), name="chat-send"),
    path("history/", views.ChatHistoryView.as_view(), name="chat-history"),
    path("clear/", views.ClearChatView.as_view(), name="chat-clear"),
]
