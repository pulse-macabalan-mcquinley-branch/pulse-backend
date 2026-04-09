"""apps/posts/admin.py"""
from django.contrib import admin
from django.utils.html import format_html

from .models import Post, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display  = ("name", "slug", "post_count")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="Posts")
    def post_count(self, obj):
        return obj.posts.count()


class TagInline(admin.TabularInline):
    model       = Post.tags.through
    extra       = 1
    verbose_name = "Tag"


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display   = (
        "title", "author", "status_badge", "is_featured",
        "views_count", "published_at", "created_at",
    )
    list_filter    = ("status", "is_featured", "created_at", "tags")
    search_fields  = ("title", "body", "author__email")
    ordering       = ("-created_at",)
    raw_id_fields  = ("author",)
    readonly_fields = ("id", "slug", "views_count", "created_at", "updated_at",
                        "published_at")
    inlines        = [TagInline]
    exclude        = ("tags",)

    fieldsets = (
        ("Content", {
            "fields": ("title", "slug", "body", "excerpt", "cover_image"),
        }),
        ("Publishing", {
            "fields": ("author", "status", "is_featured", "published_at"),
        }),
        ("Metadata", {
            "fields": ("id", "views_count", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    # ── Status badge (colored) ─────────────────────────────────
    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        colors = {
            "published": "#3fb950",
            "draft"    : "#ffa657",
            "archived" : "#8b949e",
        }
        color = colors.get(obj.status, "#8b949e")
        return format_html(
            '<span style="color:{};font-weight:600">{}</span>',
            color,
            obj.get_status_display(),
        )

    # ── Bulk actions ──────────────────────────────────────────
    actions = ["publish_posts", "unpublish_posts", "archive_posts", "feature_posts"]

    @admin.action(description="✅ Publish selected posts")
    def publish_posts(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        self.message_user(request, f"{updated} post(s) published.")

    @admin.action(description="📦 Move selected to Draft")
    def unpublish_posts(self, request, queryset):
        updated = queryset.update(status=Post.Status.DRAFT, published_at=None)
        self.message_user(request, f"{updated} post(s) moved to draft.")

    @admin.action(description="🗄 Archive selected posts")
    def archive_posts(self, request, queryset):
        updated = queryset.update(status=Post.Status.ARCHIVED)
        self.message_user(request, f"{updated} post(s) archived.")

    @admin.action(description="⭐ Toggle featured flag")
    def feature_posts(self, request, queryset):
        for post in queryset:
            post.is_featured = not post.is_featured
            post.save(update_fields=["is_featured"])
        self.message_user(request, f"{queryset.count()} post(s) updated.")