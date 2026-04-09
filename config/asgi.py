import os

import django
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

# Import after setup to avoid AppRegistryNotReady
from apps.notifications.middleware import JWTAuthMiddleware  # noqa: E402
from apps.notifications.routing import websocket_urlpatterns  # noqa: E402

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        # Standard Django HTTP handling
        "http": django_asgi_app,
        # WebSocket handling with JWT auth + allowed hosts validation
        "websocket": AllowedHostsOriginValidator(
            JWTAuthMiddleware(
                AuthMiddlewareStack(
                    URLRouter(websocket_urlpatterns)
                )
            )
        ),
    }
)