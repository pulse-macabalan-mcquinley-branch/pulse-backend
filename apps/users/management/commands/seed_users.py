import random

from django.core.management.base import BaseCommand
from faker import Faker

from apps.users.models import CustomUser

fake = Faker(["en_US", "en_PH"])


class Command(BaseCommand):
    help = "Seed the users table with fake data."

    ROLES_DISTRIBUTION = {
        CustomUser.Role.USER:       0.80,   # 80% regular users
        CustomUser.Role.ADMIN:      0.15,   # 15% admins
        CustomUser.Role.SUPERADMIN: 0.05,   # 5%  superadmins
    }

    def add_arguments(self, parser):
        parser.add_argument("--count",  type=int, default=20)
        parser.add_argument("--role",   type=str, default=None,
                            choices=[r.value for r in CustomUser.Role])
        parser.add_argument("--active-ratio", type=float, default=0.9,
                            help="Fraction of users that are active (0-1)")

    def handle(self, *args, **options):
        count        = options["count"]
        fixed_role   = options["role"]
        active_ratio = options["active_ratio"]
        created      = 0

        for i in range(count):
            role = fixed_role or self._pick_role()
            try:
                user = CustomUser.objects.create_user(
                    email      = self._unique_email(),
                    password   = "Seed@12345",   # same password for all seeded users
                    first_name = fake.first_name(),
                    last_name  = fake.last_name(),
                    role       = role,
                    is_active  = random.random() < active_ratio,
                    is_staff   = role in (CustomUser.Role.ADMIN,
                                        CustomUser.Role.SUPERADMIN),
                )
                created += 1
                if options["verbosity"] >= 1:
                    self.stdout.write(f"  + {user.email} [{role}]")
            except Exception as exc:
                self.stderr.write(f"  ! Skipped: {exc}")

        self.stdout.write(self.style.SUCCESS(
            f"  Created {created}/{count} users."
        ))

    def _pick_role(self):
        roles, weights = zip(*self.ROLES_DISTRIBUTION.items())
        return random.choices(roles, weights=weights, k=1)[0]

    def _unique_email(self, attempts=10):
        for _ in range(attempts):
            email = fake.unique.email()
            if not CustomUser.objects.filter(email=email).exists():
                return email
        raise RuntimeError("Could not generate a unique email after 10 attempts.")