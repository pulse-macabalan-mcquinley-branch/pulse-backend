"""apps/posts/filters.py"""
import django_filters

from core.filters import BaseFilterSet

from .models import Post, Tag


class PostFilterSet(BaseFilterSet):
    """
    Supported query params:
    ?status=published
    ?is_featured=true
    ?author=<uuid>
    ?tags__slug=python             (filter by single tag slug)
    ?tags=<tag-uuid>               (filter by tag id)
    ?published_after=2024-01-01
    ?published_before=2024-12-31
    ?created_after=2024-01-01
    ?min_views=100
    """

    status = django_filters.ChoiceFilter(choices=Post.Status.choices)

    is_featured = django_filters.BooleanFilter()

    author = django_filters.UUIDFilter(
        field_name="author__id",
        label="Author UUID",
    )

    author_email = django_filters.CharFilter(
        field_name="author__email",
        lookup_expr="icontains",
        label="Author email (partial)",
    )

    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        label="Tags (by UUID)",
    )

    tags__slug = django_filters.CharFilter(
        field_name="tags__slug",
        lookup_expr="exact",
        label="Tag slug",
    )

    published_after = django_filters.DateFilter(
        field_name="published_at",
        lookup_expr="date__gte",
        label="Published after (YYYY-MM-DD)",
    )

    published_before = django_filters.DateFilter(
        field_name="published_at",
        lookup_expr="date__lte",
        label="Published before (YYYY-MM-DD)",
    )

    min_views = django_filters.NumberFilter(
        field_name="views_count",
        lookup_expr="gte",
        label="Minimum views",
    )

    class Meta:
        model  = Post
        fields = [
            "status", "is_featured", "author",
            "author_email", "tags", "tags__slug",
            "published_after", "published_before",
            "min_views", "created_after", "created_before",
        ]