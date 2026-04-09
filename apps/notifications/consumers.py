import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    Connect: ws://host/ws/notifications/?token=<access_jwt>
    Group name: notifications_<user_uuid>
    """

    async def connect(self):
        self.user = self.scope.get("user")

        # JWTAuthMiddleware sets user; reject anonymous connections
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.group_name = f"notifications_{self.user.pk}"

        # Join the user-specific group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        logger.info("WS connected: user=%s group=%s", self.user.pk, self.group_name)

        # Send unread notification count on connect
        unread = await self.get_unread_count()
        await self.send_json({"type": "init", "unread_count": unread})

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info("WS disconnected: code=%s", close_code)

    async def receive_json(self, content):
        """Handle messages from the client (e.g., mark-as-read)."""
        msg_type = content.get("type")

        if msg_type == "mark_read":
            notification_id = content.get("id")
            if notification_id:
                await self.mark_notification_read(notification_id)
                await self.send_json({"type": "marked_read", "id": notification_id})

    # ── Channel layer handler: called by group_send ───────────
    async def notification_push(self, event):
        """
        Triggered by:
        channel_layer.group_send(group_name, {
            "type": "notification.push",
            "payload": {...}
        })
        Note: Channels converts '.' to '_' in type names.
        """
        await self.send_json({
            "type": "notification",
            "payload": event["payload"],
        })

    # ── DB helpers (sync → async) ─────────────────────────────
    @database_sync_to_async
    def get_unread_count(self):
        from .models import Notification
        return Notification.objects.filter(user=self.user, is_read=False).count()

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        from .models import Notification
        Notification.objects.filter(
            pk=notification_id, user=self.user
        ).update(is_read=True)