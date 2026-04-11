"""
factories.py — factory_boy model factories for testing.
Place in project root or per-app as needed.

Usage in tests:
    from factories import UserFactory, PostFactory, AdminFactory

    user  = UserFactory()                       # unsaved
    user  = UserFactory.create()                # saved
    users = UserFactory.create_batch(10)        # 10 saved users
    admin = AdminFactory()                      # role='admin', is_staff=True
    post  = PostFactory(author=user)            # post with specific author
    draft = PostFactory(status='draft')
"""
import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory, ImageField

from apps.posts.models import Post, Tag

User = get_user_model()


# ── User factories ────────────────────────────────────────────
class UserFactory(DjangoModelFactory):
    """Creates a regular active user with a unique email."""

    class Meta:
        model = User
        django_get_or_create = ("email",)
        skip_postgeneration_save = True

    email      = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name  = factory.Faker("last_name")
    password   = factory.PostGenerationMethodCall("set_password", "Test@1234")
    role       = User.Role.USER
    is_active  = True
    is_staff   = False

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.groups.add(*extracted)


class AdminFactory(UserFactory):
    """Creates an admin user."""
    email    = factory.Sequence(lambda n: f"admin{n}@example.com")
    role     = User.Role.ADMIN
    is_staff = True


class SuperAdminFactory(UserFactory):
    """Creates a superadmin user."""
    email        = factory.Sequence(lambda n: f"superadmin{n}@example.com")
    role         = User.Role.SUPERADMIN
    is_staff     = True
    is_superuser = True


class InactiveUserFactory(UserFactory):
    """Creates an inactive (deactivated) user."""
    email     = factory.Sequence(lambda n: f"inactive{n}@example.com")
    is_active = False


# ── Tag factory ───────────────────────────────────────────────
class TagFactory(DjangoModelFactory):
    class Meta:
        model = Tag
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"tag-{n}")
    slug = factory.LazyAttribute(lambda o: o.name.lower().replace(" ", "-"))


# ── Post factories ────────────────────────────────────────────
class PostFactory(DjangoModelFactory):
    """Creates a published post with a random author."""

    class Meta:
        model = Post
        django_get_or_create = ("slug",)
        skip_postgeneration_save = True

    title       = factory.Faker("sentence", nb_words=6)
    slug        = factory.Sequence(lambda n: f"post-slug-{n}")
    body        = factory.Faker("paragraphs", nb=4, as_text=True)
    author      = factory.SubFactory(UserFactory)
    status      = Post.Status.PUBLISHED
    is_featured = False

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        """
        Usage:
            PostFactory(tags=[tag1, tag2])
            PostFactory(tags=TagFactory.create_batch(3))
        """
        if not create:
            return
        if extracted:
            self.tags.set(extracted)
        else:
            # Auto-assign 1-3 random tags
            self.tags.set(TagFactory.create_batch(
                factory.random.randgen.randint(1, 3)
            ))


class DraftPostFactory(PostFactory):
    status = Post.Status.DRAFT


class FeaturedPostFactory(PostFactory):
    is_featured = True