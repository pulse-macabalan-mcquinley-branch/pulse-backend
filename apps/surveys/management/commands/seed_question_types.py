from django.core.management.base import BaseCommand

from apps.surveys.models import QuestionType

class Command(BaseCommand):
    help = "Seed the question types table with predefined types." 

    def handle(self, *args, **options):
        question_types = [
            {"code": "text", "name": "Text"},
            {"code": "single_choice", "name": "Single Choice"},
            {"code": "multiple_choice", "name": "Multiple Choice"},
            {"code": "checkboxes", "name": "Checkboxes"},
            {"code": "rating", "name": "Rating"},
            {"code": "numeric", "name": "Numeric"},
            {"code": "matrix", "name": "Matrix"},
            {"code": "data", "name": "Data"},
            {"code": "geo", "name": "Geo"},
            {"code": "file_upload", "name": "File Upload"},
        ]

        created = 0
        for qt in question_types:
            obj, was_created = QuestionType.objects.get_or_create(
                code=qt["code"],
                defaults={"name": qt["name"]}
            )
            if was_created:
                created += 1
                self.stdout.write(f"  + Created: {obj.code} - {obj.name}")
            else:
                self.stdout.write(f"  - Exists: {obj.code} - {obj.name}")

        self.stdout.write(self.style.SUCCESS(
            f"  Seeded {created}/{len(question_types)} question types."
        ))