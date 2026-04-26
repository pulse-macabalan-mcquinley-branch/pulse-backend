# apps/surveys/tasks.py
from celery_app.celery import shared_task
from django.utils import timezone


@shared_task(name="apps.surveys.tasks.publish_scheduled_surveys")
def publish_scheduled_surveys():
    from .models import Survey

    Survey.objects.filter(
        status=Survey.Status.DRAFT,
        scheduled_publish_at__isnull=False,
        scheduled_publish_at__lte=timezone.now(),
    ).update(
        status=Survey.Status.PUBLISHED,
        published_at=timezone.now(),
        scheduled_publish_at=None,
    )


@shared_task(name="apps.surveys.tasks.close_scheduled_surveys")
def close_scheduled_surveys():
    from .models import Survey

    Survey.objects.filter(
        status=Survey.Status.PUBLISHED,
        scheduled_closed_at__isnull=False,
        scheduled_closed_at__lte=timezone.now(),
    ).update(
        status=Survey.Status.CLOSED,
        scheduled_closed_at=None,
    )