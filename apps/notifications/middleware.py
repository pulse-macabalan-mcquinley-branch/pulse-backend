from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken


class JWTAuthMiddleware(BaseMiddleware):
    """
    Authenticates WebSocket connections using a JWT access token
    passed as a query parameter: ?token=<access_token>
    """

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        params       = parse_qs(query_string)
        token_list   = params.get("token", [])

        scope["user"] = AnonymousUser()

        if token_list:
            scope["user"] = await self.get_user(token_list[0])

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user(self, token_str):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            token = AccessToken(token_str)
            return User.objects.get(pk=token["user_id"])
        except (InvalidToken, TokenError, User.DoesNotExist):
            return AnonymousUser()