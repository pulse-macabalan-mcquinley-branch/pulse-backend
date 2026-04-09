from django.urls import path

from .consumers import NotificationConsumer

websocket_urlpatterns = [
    # ws://localhost:8000/ws/notifications/?token=<jwt>
    path("ws/notifications/", NotificationConsumer.as_asgi()),
]