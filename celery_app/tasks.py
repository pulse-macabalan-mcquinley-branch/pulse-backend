import logging

from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    name="tasks.send_email",
)
def send_email_task(self, subject, message, recipient_list, html_message=None):
    """
    Generic async email task.
    Usage: send_email_task.delay(subject, message, ["user@example.com"])
    """
    try:
        send_mail(
            subject      = subject,
            message      = message,
            from_email   = settings.DEFAULT_FROM_EMAIL,
            recipient_list = recipient_list,
            html_message = html_message,
            fail_silently = False,
        )
        logger.info("Email sent to %s | subject: %s", recipient_list, subject)
    except Exception as exc:
        logger.error("Email send failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(name="tasks.send_welcome_email")
def send_welcome_email(user_id):
    """
    Triggered via signal in apps/users/signals.py after user registration.
    """
    try:
        user = User.objects.get(pk=user_id)
        send_email_task.delay(
            subject        = f"Welcome to {settings.SPECTACULAR_SETTINGS['TITLE']}!",
            message        = f"Hi {user.first_name},\\n\\nWelcome aboard!",
            recipient_list = [user.email],
        )
    except User.DoesNotExist:
        logger.warning("send_welcome_email: User %s not found", user_id)


@shared_task(name="tasks.flush_expired_tokens")
def flush_expired_tokens():
    """Periodic task: flush blacklisted + expired SimpleJWT tokens."""
    from rest_framework_simplejwt.token_blacklist.management.commands import (
        flushexpiredtokens,
    )
    flushexpiredtokens.Command().handle()
    logger.info("Expired JWT tokens flushed.")