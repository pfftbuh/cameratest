from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/proctor/(?P<session_id>[\w-]+)/$', consumers.ProctorConsumer.as_asgi()),
    re_path(r'^ws/monitor/(?P<exam_id>[\w-]+)/$', consumers.MonitorConsumer.as_asgi()),
]
