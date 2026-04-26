import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.surveys.models import Survey, Response, Answer, Question, DeviceType
from apps.users.models import CustomUser
from faker import Faker

fake = Faker(["en_US", "en_PH"])


class Command(BaseCommand):
    help = "Seed responses and answers for published surveys."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=30)

    def handle(self, *args, **options):
        count = options["count"]

        published_surveys = list(Survey.objects.filter(status=Survey.Status.PUBLISHED))
        if not published_surveys:
            self.stderr.write("  ! No published surveys found. Run seed_surveys first.")
            return

        users       = list(CustomUser.objects.filter(is_active=True))
        device_types = list(DeviceType.objects.all())

        if not device_types:
            self.stderr.write("  ! No device types found. Run seed_device_types first.")
            return

        created = 0
        for _ in range(count):
            survey    = random.choice(published_surveys)
            user      = random.choice(users) if not survey.allow_anonymous else None
            questions = list(survey.questions.select_related("type").prefetch_related("options").all())

            if not questions:
                continue

            response = Response.objects.create(
                survey               = survey,
                submitted_by         = user,
                device_type          = random.choice(device_types),
                status               = Response.Status.COMPLETE,
                duration_seconds     = random.randint(30, 600),
                is_flagged           = random.random() < 0.05,
                flag_reason          = "Suspiciously fast completion" if random.random() < 0.05 else None,
                is_offline_submitted = random.choice([True, False]),
                submitted_at         = timezone.now(),
                ip_address           = fake.ipv4(),
            )

            answers = []
            for question in questions:
                code = question.type.code.lower()
                was_skipped = not question.is_required and random.random() < 0.2

                answer = Answer(
                    response=response,
                    question=question,
                    was_skipped=was_skipped,
                )

                if not was_skipped:
                    if code == "text":
                        answer.answer_text = fake.paragraph(nb_sentences=2)
                    elif code in ("single_choice", "checkboxes"):
                        opts = list(question.options.values_list("option_value", flat=True))
                        if opts:
                            if code == "single_choice":
                                answer.answer_json = random.choice(opts)
                            else:
                                answer.answer_json = random.sample(opts, k=random.randint(1, len(opts)))
                    elif code in ("numeric", "rating"):
                        lo = int(question.min_value or 1)
                        hi = int(question.max_value or 10)
                        answer.answer_number = random.randint(lo, hi)
                    elif code == "file_upload":
                        answer.file_url = fake.image_url()

                answers.append(answer)

            Answer.objects.bulk_create(answers)
            created += 1
            self.stdout.write(f"  + Response for '{survey.title}' by {user.email if user else 'anonymous'}")

        self.stdout.write(self.style.SUCCESS(f"  Created {created}/{count} responses."))