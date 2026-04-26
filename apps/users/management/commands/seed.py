"""
apps/users/management/commands/seed.py
Master seed command that calls every app-level seeder in the right order.

Usage:
    python manage.py seed                     # seed everything (dev defaults)
    python manage.py seed --users 50          # 50 users
    python manage.py seed --posts 200         # 200 posts
    python manage.py seed --fresh             # wipe + reseed
    python manage.py seed --env production    # load production fixture only
"""
import logging
import time

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with realistic development/testing data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--users",
            type=int,
            default=20,
            help="Number of regular users to create (default: 20)",
        )
        parser.add_argument(
            "--posts",
            type=int,
            default=50,
            help="Number of posts to create (default: 50)",
        )
        parser.add_argument(
            "--fresh",
            action="store_true",
            help="Wipe existing seed data before seeding",
        )
        parser.add_argument(
            "--env",
            choices=["development", "production"],
            default="development",
            help="Seed profile (default: development)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        start = time.time()
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\\n🌱  Starting seed [{options['env']}] ..."
        ))

        if options["fresh"]:
            self._wipe()

        if options["env"] == "production":
            self._seed_production()
        else:
            self._seed_development(
                user_count=options["users"],
                post_count=options["posts"],
            )

        elapsed = time.time() - start
        self.stdout.write(self.style.SUCCESS(
            f"\\n✅  Seeding complete in {elapsed:.2f}s"
        ))

    # ── Wipe ─────────────────────────────────────────────────
    def _wipe(self):
        self.stdout.write("  Wiping existing seed data...")
        # from apps.notifications.models import Notification
        from apps.surveys.models import (
            Survey, Question, QuestionOption,
            Response, Answer,
        )

        Answer.objects.all().delete()
        Response.objects.all().delete()
        QuestionOption.objects.all().delete()
        Question.objects.all().delete()
        Survey.objects.all().delete()
        # Notification.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write(self.style.WARNING("  ⚠  Seed data cleared."))

    # ── Development seed ──────────────────────────────────────
    def _seed_development(self, user_count, post_count):
        self.stdout.write("  [1/6] Seeding superadmin...")
        self._ensure_superadmin()

        self.stdout.write(f"  [2/6] Seeding {user_count} users...")
        call_command("seed_users", count=user_count, verbosity=0)

        self.stdout.write("  [3/6] Seeding question types...")
        call_command("seed_question_types", verbosity=0)

        self.stdout.write("  [4/6] Seeding device types...")
        call_command("seed_device_types", verbosity=0)

        self.stdout.write("  [5/6] Seeding surveys...")
        call_command("seed_surveys", count=10, verbosity=0)

        self.stdout.write("  [6/6] Seeding responses...")
        call_command("seed_responses", count=50, verbosity=0)

    # ── Production seed (safe, idempotent) ───────────────────
    def _seed_production(self):
        self.stdout.write("  Loading production fixtures...")
        call_command("loaddata", "fixtures/production_roles.json")

        self.stdout.write("  Ensuring superadmin exists...")
        call_command("seed_question_types", verbosity=0)
        call_command("seed_device_types", verbosity=0)

        self._ensure_superadmin()

    # ── Helpers ───────────────────────────────────────────────
    def _ensure_superadmin(self):
        email = "admin@example.com"
        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(
                email      = email,
                password   = "Admin@12345",
                first_name = "Super",
                last_name  = "Admin",
            )
            self.stdout.write(self.style.SUCCESS(
                f"     Created superadmin: {email} / Admin@12345"
            ))
        else:
            self.stdout.write(f"     Superadmin {email} already exists — skipped.")