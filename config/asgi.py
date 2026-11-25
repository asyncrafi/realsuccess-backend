"""
ASGI config for Real Success project.

It exposes the ASGI callable as a module-level variable named ``application``.
"""

import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

http_application = get_asgi_application()

try:
    from channels.routing import ProtocolTypeRouter, URLRouter
    from apps.message_team.middleware import JWTAuthMiddleware
    from apps.message_team.routing import websocket_urlpatterns

    application = ProtocolTypeRouter({
        "http": http_application,
        "websocket": JWTAuthMiddleware(
            URLRouter(websocket_urlpatterns)
        ),
    })
except ImportError:
    application = http_application
