import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("django_app")

# Load config from Django settings, namespace 'CELERY_'
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in every installed app
app.autodiscover_tasks()

# ── Periodic tasks (stored in DB via django-celery-beat) ──────
app.conf.beat_schedule = {
    # Example: clean expired tokens every night at 2 AM
    "flush-expired-tokens": {
        "task"     : "apps.users.tasks.flush_expired_tokens",
        "schedule" : crontab(hour=2, minute=0),
    },
    # Example: send weekly digest every Monday 8 AM
    "weekly-digest": {
        "task"     : "apps.notifications.tasks.send_weekly_digest",
        "schedule" : crontab(day_of_week=1, hour=8, minute=0),
    },
}

app.conf.task_routes = {
    "apps.users.tasks.*"         : {"queue": "default"},
    "apps.notifications.tasks.*" : {"queue": "notifications"},
}

app.conf.broker_connection_retry_on_startup = True


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Health check task — celery inspect call debug_task."""
    print(f"Request: {self.request!r}")