from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Notification
        fields = ["id", "type", "title", "body", "payload", "is_read", "created_at"]
        read_only_fields = ["id", "created_at"]


def push_notification_to_user(user, notification_type, title, body, payload=None):
    """
    Helper: create DB notification record and push to WebSocket group.
    Safe to call from synchronous code (Celery tasks, signals, etc).

    Usage:
        push_notification_to_user(
            user=user_obj,
            notification_type="order_update",
            title="Order shipped",
            body="Your order #1234 has been shipped.",
            payload={"order_id": 1234},
        )
    """
    notification = Notification.objects.create(
        user    = user,
        type    = notification_type,
        title   = title,
        body    = body,
        payload = payload or {},
    )

    channel_layer = get_channel_layer()
    group_name    = f"notifications_{user.pk}"

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "notification.push",
            "payload": NotificationSerializer(notification).data,
        },
    )

    return notification