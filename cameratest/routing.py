import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cameratest.settings")

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import mycamera.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(mycamera.routing.websocket_urlpatterns),
})
