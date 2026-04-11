from django.core.management.base import BaseCommand

from apps.surveys.models import DeviceType

class Command(BaseCommand):
    help = "Seed the device types table with predefined types."

    def handle(self, *args, **options):
        device_types = [
            {"code": "mobile", "name": "Mobile"},
            {"code": "desktop", "name": "Desktop"},
            {"code": "tablet", "name": "Tablet"},
        ]

        created = 0
        for dt in device_types:
            obj, was_created = DeviceType.objects.get_or_create(
                code=dt["code"],
                defaults={"name": dt["name"]}
            )
            if was_created:
                created += 1
                self.stdout.write(f"  + Created: {obj.code} - {obj.name}")
            else:
                self.stdout.write(f"  - Exists: {obj.code} - {obj.name}")
        
        self.stdout.write(self.style.SUCCESS(
            f"  Seeded {created}/{len(device_types)} device types."
        ))