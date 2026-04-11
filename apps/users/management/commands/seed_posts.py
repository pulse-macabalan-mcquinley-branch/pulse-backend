SEED_POSTS_CODE = ''
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker
from apps.posts.models import Post, Tag

fake = Faker()
User = get_user_model()

class Command(BaseCommand):
    help = "Seed the posts table with fake data."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=50)

    def handle(self, *args, **options):
        users = list(User.objects.filter(is_active=True))
        if not users:
            self.stderr.write("No active users found. Run seed_users first.")
            return

        # Ensure some tags exist
        tag_names = ["python","django","api","backend","tutorial",
                    "devops","testing","security","performance","async"]
        tags = [Tag.objects.get_or_create(name=t, slug=t)[0] for t in tag_names]

        created = 0
        for _ in range(options["count"]):
            post = Post.objects.create(
                title   = fake.sentence(nb_words=random.randint(4, 10)).rstrip("."),
                slug    = fake.unique.slug(),
                body    = "\\n\\n".join(fake.paragraphs(nb=random.randint(3, 8))),
                author  = random.choice(users),
                status  = random.choice(["draft", "draft", "published"]),
                is_featured = random.random() < 0.1,
            )
            post.tags.set(random.sample(tags, k=random.randint(1, 4)))
            created += 1

        self.stdout.write(self.style.SUCCESS(f"  Created {created} posts."))