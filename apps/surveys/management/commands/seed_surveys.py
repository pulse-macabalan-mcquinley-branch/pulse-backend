import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
from apps.surveys.models import Survey, Question, QuestionType, QuestionOption
from apps.users.models import CustomUser

fake = Faker(["en_US", "en_PH"])


class Command(BaseCommand):
    help = "Seed surveys with questions and options."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=10)

    def handle(self, *args, **options):
        count = options["count"]

        researchers = list(CustomUser.objects.filter(role=CustomUser.Role.RESEARCHER))
        if not researchers:
            self.stderr.write("  ! No researchers found. Run seed_users first.")
            return

        text_type        = QuestionType.objects.get(code="text")
        single_type      = QuestionType.objects.get(code="single_choice")
        checkboxes_type  = QuestionType.objects.get(code="checkboxes")
        numeric_type     = QuestionType.objects.get(code="numeric")
        rating_type      = QuestionType.objects.get(code="rating")
        file_type        = QuestionType.objects.get(code="file_upload")

        created = 0
        for _ in range(count):
            owner  = random.choice(researchers)
            status = random.choice([
                Survey.Status.DRAFT,
                Survey.Status.PUBLISHED,
                Survey.Status.CLOSED,
            ])
            published_at = timezone.now() if status in (
                Survey.Status.PUBLISHED, Survey.Status.CLOSED
            ) else None

            survey = Survey.objects.create(
                created_by            = owner,
                title                 = fake.sentence(nb_words=6).rstrip("."),
                description           = fake.paragraph(nb_sentences=2),
                status                = status,
                offline_enabled       = random.choice([True, False]),
                allow_anonymous       = random.choice([True, False]),
                one_response_per_user = random.choice([True, False]),
                response_limit        = random.choice([None, 100, 500, 1000]),
                show_progress_bar     = random.choice([True, False]),
                published_at          = published_at,
                closes_at             = (
                    timezone.now() + timezone.timedelta(days=random.randint(7, 90))
                    if status == Survey.Status.PUBLISHED else None
                ),
            )

            self._seed_questions(survey, text_type, single_type, checkboxes_type, numeric_type, rating_type, file_type)
            created += 1
            self.stdout.write(f"  + Survey: '{survey.title}' [{status}] by {owner.email}")

        self.stdout.write(self.style.SUCCESS(f"  Created {created}/{count} surveys."))

    def _seed_questions(self, survey, text_type, single_type, checkboxes_type, numeric_type, rating_type, file_type):
        questions = [
            {
                "type": text_type,
                "question_text": "Describe your overall experience.",
                "helper_text": "You may write in Filipino or English.",
                "display_order": 1,
                "is_required": True,
                "max_length": 500,
            },
            {
                "type": single_type,
                "question_text": "What is your primary source of income?",
                "helper_text": None,
                "display_order": 2,
                "is_required": True,
            },
            {
                "type": checkboxes_type,
                "question_text": "Which government services have you used?",
                "helper_text": "Select all that apply.",
                "display_order": 3,
                "is_required": False,
            },
            {
                "type": numeric_type,
                "question_text": "How many people live in your household?",
                "helper_text": "Include all family members.",
                "display_order": 4,
                "is_required": True,
                "min_value": 1,
                "max_value": 20,
            },
            {
                "type": rating_type,
                "question_text": "Rate the quality of service you received.",
                "helper_text": "1 = Poor, 5 = Excellent.",
                "display_order": 5,
                "is_required": True,
                "min_value": 1,
                "max_value": 5,
            },
            {
                "type": file_type,
                "question_text": "Upload a photo of your household's water source.",
                "helper_text": "Accepted formats: JPG, PNG, PDF.",
                "display_order": 6,
                "is_required": False,
            },
        ]

        for q_data in questions:
            options_data = q_data.pop("options", [])
            question = Question.objects.create(survey=survey, **q_data)
            self._seed_options(question, options_data)

        # ── Attach options to single_choice and checkboxes ────
        single_q = Question.objects.get(
            survey=survey, question_text="What is your primary source of income?"
        )
        self._seed_options(single_q, [
            {"option_text": "Employed (private)",       "option_value": "employed_private", "display_order": 1},
            {"option_text": "Employed (government)",    "option_value": "employed_govt",    "display_order": 2},
            {"option_text": "Self-employed / Informal", "option_value": "self_employed",    "display_order": 3},
            {"option_text": "No income",                "option_value": "no_income",        "display_order": 4},
            {"option_text": "Other (please specify)",   "option_value": "other",            "display_order": 5, "is_other": True},
        ])

        check_q = Question.objects.get(
            survey=survey, question_text="Which government services have you used?"
        )
        self._seed_options(check_q, [
            {"option_text": "PhilHealth", "option_value": "philhealth", "display_order": 1},
            {"option_text": "SSS",        "option_value": "sss",        "display_order": 2},
            {"option_text": "Pag-IBIG",   "option_value": "pagibig",    "display_order": 3},
            {"option_text": "4Ps",        "option_value": "4ps",        "display_order": 4},
            {"option_text": "GSIS",       "option_value": "gsis",       "display_order": 5},
        ])

    def _seed_options(self, question, options_data):
        QuestionOption.objects.bulk_create([
            QuestionOption(question=question, **opt)
            for opt in options_data
        ])