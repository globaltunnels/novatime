from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Live updates WebSocket
    re_path(
        r'ws/live-updates/(?P<workspace_id>[0-9a-f-]+)/$',
        consumers.LiveUpdatesConsumer.as_asgi()
    ),
    
    # Chat WebSocket  
    re_path(
        r'ws/chat/(?P<workspace_id>[0-9a-f-]+)/(?P<room_type>\w+)/(?P<room_id>[0-9a-f-]+)/$',
        consumers.ChatConsumer.as_asgi()
    ),
]