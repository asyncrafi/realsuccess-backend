from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_key):
    try:
        access_token = AccessToken(token_key)
        user_id = access_token["user_id"]
        return User.objects.get(id=user_id)
    except Exception:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Authenticates WebSocket connections using ?token=<jwt_access_token>
    or the Authorization: Bearer <token> header.
    """

    async def __call__(self, scope, receive, send):
        token = None

        # 1. Check query string (?token=...)
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        if "token" in query_params and query_params["token"]:
            token = query_params["token"][0]

        # 2. Fallback to Authorization header
        if not token:
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode("utf-8")
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1].strip()

        scope["user"] = await get_user_from_token(token) if token else AnonymousUser()
        return await super().__call__(scope, receive, send)
