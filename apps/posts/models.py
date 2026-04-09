"""
apps/posts/models.py
Complete post/article model demonstrating:
- BaseModel (UUID pk + timestamps)
- TextChoices status enum
- SlugField with auto-generation
- ManyToMany tags
- Author FK to AUTH_USER_MODEL
- Computed properties & QuerySet helpers
"""
from django.conf import settings
from django.db import models
from django.utils.text import slugify

from core.models import BaseModel


class Tag(BaseModel):
    """Lightweight taxonomy tag for posts."""

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, db_index=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "tags"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class PostQuerySet(models.QuerySet):
    """Custom queryset with business-logic shortcuts."""

    def published(self):
        return self.filter(status=Post.Status.PUBLISHED)

    def drafts(self):
        return self.filter(status=Post.Status.DRAFT)

    def featured(self):
        return self.filter(is_featured=True, status=Post.Status.PUBLISHED)

    def by_author(self, user):
        return self.filter(author=user)

    def with_tag(self, slug):
        return self.filter(tags__slug=slug)

    def search(self, query):
        from django.db.models import Q
        return self.filter(
            Q(title__icontains=query)
            | Q(body__icontains=query)
            | Q(tags__name__icontains=query)
        ).distinct()


class Post(BaseModel):
    """
    Blog/article post.
    CRUD endpoints:
    GET    /api/v1/posts/           → list (published; drafts for author/admin)
    POST   /api/v1/posts/           → create (auth required)
    GET    /api/v1/posts/{id}/      → retrieve
    PUT    /api/v1/posts/{id}/      → full update  (owner/admin)
    PATCH  /api/v1/posts/{id}/      → partial update (owner/admin)
    DELETE /api/v1/posts/{id}/      → destroy (owner/admin)
    POST   /api/v1/posts/{id}/publish/  → publish action
    POST   /api/v1/posts/{id}/feature/  → feature toggle (admin)
    """

    class Status(models.TextChoices):
        DRAFT     = "draft",     "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED  = "archived",  "Archived"

    # ── Core fields ───────────────────────────────────────────
    title       = models.CharField(max_length=255, db_index=True)
    slug        = models.SlugField(max_length=280, unique=True, db_index=True,
                                    blank=True)
    body        = models.TextField()
    excerpt     = models.CharField(max_length=500, blank=True,
                                    help_text="Auto-generated if left blank")
    cover_image = models.ImageField(upload_to="posts/covers/%Y/%m/",
                                    null=True, blank=True)

    # ── Relations ─────────────────────────────────────────────
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="posts",
        db_index=True,
    )
    tags = models.ManyToManyField(Tag, related_name="posts", blank=True)

    # ── Status & meta ─────────────────────────────────────────
    status      = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    is_featured  = models.BooleanField(default=False, db_index=True)
    views_count  = models.PositiveIntegerField(default=0, editable=False)
    published_at = models.DateTimeField(null=True, blank=True)

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "is_featured"]),
            models.Index(fields=["author", "status"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Auto-generate slug from title
        if not self.slug:
            base = slugify(self.title)[:270]
            slug, n = base, 1
            while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug

        # Auto-generate excerpt
        if not self.excerpt and self.body:
            self.excerpt = self.body[:500].rsplit(" ", 1)[0] + "..."

        # Set published_at when first published
        if self.status == self.Status.PUBLISHED and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    # ── Computed properties ───────────────────────────────────
    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED

    @property
    def reading_time_minutes(self):
        """Approx reading time at 200 wpm."""
        word_count = len(self.body.split())
        return max(1, round(word_count / 200))