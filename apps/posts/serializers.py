"""apps/posts/serializers.py"""
from rest_framework import serializers

from apps.users.serializers import UserSerializer

from .models import Post, Tag


# ── Tag ───────────────────────────────────────────────────────
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Tag
        fields = ["id", "name", "slug"]
        read_only_fields = ["id", "slug"]


class TagSlugRelatedField(serializers.SlugRelatedField):
    """Accept tags by slug in write operations: ["python", "django"]"""

    def to_internal_value(self, data):
        try:
            return self.get_queryset().get(slug=data)
        except Tag.DoesNotExist:
            self.fail("does_not_exist", slug_name="slug", value=data)


# ── Post: List (lightweight) ──────────────────────────────────
class PostListSerializer(serializers.ModelSerializer):
    """Lean representation for list endpoints — no full body."""

    author          = UserSerializer(read_only=True)
    tags            = TagSerializer(many=True, read_only=True)
    reading_time    = serializers.IntegerField(
        source="reading_time_minutes", read_only=True
    )

    class Meta:
        model  = Post
        fields = [
            "id", "title", "slug", "excerpt", "cover_image",
            "author", "tags", "status", "is_featured",
            "views_count", "reading_time", "published_at", "created_at",
        ]


# ── Post: Detail (full body) ──────────────────────────────────
class PostDetailSerializer(PostListSerializer):
    """Full post including body — used on retrieve."""

    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + ["body", "updated_at"]


# ── Post: Write (create / update) ────────────────────────────
class PostWriteSerializer(serializers.ModelSerializer):
    """
    Accepts tags as list of slugs:
    {"title": "...", "body": "...", "tags": ["python", "django"]}
    """

    tags = TagSlugRelatedField(
        many=True,
        slug_field="slug",
        queryset=Tag.objects.all(),
        required=False,
    )

    class Meta:
        model  = Post
        fields = [
            "title", "body", "excerpt", "cover_image", "tags",
            "status", "is_featured",
        ]

    def validate_status(self, value):
        """Only admins/superadmins can directly set status to published."""
        request = self.context.get("request")
        if (value == Post.Status.PUBLISHED
                and request
                and not request.user.is_admin):
            raise serializers.ValidationError(
                "Only admins can publish posts directly. "
                "Use the /publish/ action instead."
            )
        return value

    def validate_title(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError(
                "Title must be at least 5 characters."
            )
        return value.strip()

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        post = Post.objects.create(**validated_data)
        post.tags.set(tags)
        return post

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            instance.tags.set(tags)
        return instance