from django.urls import path
from .views import (
    ChatView,
    ChatContentAJAXView,
)

app_name = 'chat'

urlpatterns = [
    path('', ChatView.as_view(), name='messages'),
    path('chat-content/<str:room_name>/', ChatContentAJAXView.as_view(), name='chat_content'),
]
