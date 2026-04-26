# apps/surveys/migrations/0002_seed_beat_schedules.py
from django.db import migrations


def seed_schedules(apps, schema_editor):
    IntervalSchedule = apps.get_model("django_celery_beat", "IntervalSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    every_minute, _ = IntervalSchedule.objects.get_or_create(
        every=1,
        period="minutes",   # ← string directly, not IntervalSchedule.MINUTES
    )
    PeriodicTask.objects.get_or_create(
        name="Publish scheduled surveys",
        defaults={
            "task": "apps.surveys.tasks.publish_scheduled_surveys",
            "interval": every_minute,
            "enabled": True,
        }
    )
    PeriodicTask.objects.get_or_create(
        name="Close scheduled surveys",
        defaults={
            "task": "apps.surveys.tasks.close_scheduled_surveys",
            "interval": every_minute,
            "enabled": True,
        }
    )


def remove_schedules(apps, schema_editor):
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    PeriodicTask.objects.filter(name__in=[
        "Publish scheduled surveys",
        "Close scheduled surveys",
    ]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("surveys", "0001_initial"),
        ("django_celery_beat", "0018_improve_crontab_helptext"),
    ]
    operations = [
        migrations.RunPython(seed_schedules, remove_schedules)
    ]