"""
ASGI config for Real Success project.

It exposes the ASGI callable as a module-level variable named ``application``.
"""

import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

try:
    from channels.routing import ProtocolTypeRouter, URLRouter
    application = ProtocolTypeRouter({
        "http": get_asgi_application(),
    })
except ImportError:
    application = get_asgi_application()
