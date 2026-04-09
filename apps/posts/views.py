"""
apps/posts/views.py
Complete CRUD ViewSet for Post:

Method  Endpoint                        Action
──────────────────────────────────────────────────
GET     /api/v1/posts/                  list
POST    /api/v1/posts/                  create
GET     /api/v1/posts/{id}/             retrieve
PUT     /api/v1/posts/{id}/             update
PATCH   /api/v1/posts/{id}/             partial_update
DELETE  /api/v1/posts/{id}/             destroy
POST    /api/v1/posts/{id}/publish/     publish
POST    /api/v1/posts/{id}/unpublish/   unpublish
POST    /api/v1/posts/{id}/feature/     feature toggle
GET     /api/v1/posts/my-posts/         list own posts
GET     /api/v1/tags/                   tag list (read-only)
"""
from django.db.models import F
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from core.pagination import StandardResultsPagination
from core.permissions import IsOwnerOrAdmin

from .filters import PostFilterSet
from .models import Post, Tag
from .serializers import (
    PostDetailSerializer,
    PostListSerializer,
    PostWriteSerializer,
    TagSerializer,
)


@extend_schema_view(
    list    = extend_schema(summary="List published posts"),
    create  = extend_schema(summary="Create a new post"),
    retrieve= extend_schema(summary="Get post detail"),
    update  = extend_schema(summary="Full update a post"),
    partial_update = extend_schema(summary="Partial update a post"),
    destroy = extend_schema(summary="Delete a post"),
)
class PostViewSet(ModelViewSet):
    """
    Full CRUD for posts.
    - Unauthenticated users see only published posts.
    - Authenticated authors see their own drafts + all published.
    - Admins see everything.
    """

    pagination_class = StandardResultsPagination
    filterset_class  = PostFilterSet
    search_fields    = ["title", "body", "tags__name", "author__email"]
    ordering_fields  = ["created_at", "published_at", "views_count", "title"]
    ordering         = ["-created_at"]

    # ── Queryset scoping ──────────────────────────────────────
    def get_queryset(self):
        user = self.request.user

        qs = Post.objects.select_related("author").prefetch_related("tags")

        if not user.is_authenticated:
            return qs.published()

        if user.is_admin:
            return qs.all()

        # Regular user: own posts (any status) + other's published
        from django.db.models import Q
        return qs.filter(
            Q(author=user) | Q(status=Post.Status.PUBLISHED)
        ).distinct()

    # ── Serializer selection ──────────────────────────────────
    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return PostWriteSerializer
        if self.action == "retrieve":
            return PostDetailSerializer
        return PostListSerializer

    # ── Permissions ───────────────────────────────────────────
    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        if self.action in ("update", "partial_update", "destroy",
                            "publish", "unpublish"):
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        if self.action == "feature":
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]

    # ── Set author automatically on create ───────────────────
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    # ── Increment view count on retrieve ─────────────────────
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Atomic increment — race-condition safe
        Post.objects.filter(pk=instance.pk).update(
            views_count=F("views_count") + 1
        )
        instance.refresh_from_db(fields=["views_count"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    # ── Custom actions ────────────────────────────────────────

    @extend_schema(responses={200: PostDetailSerializer})
    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        """Publish a draft post. Only the author or an admin can do this."""
        post = self.get_object()
        if post.status == Post.Status.PUBLISHED:
            return Response(
                {"detail": "Post is already published."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        post.status = Post.Status.PUBLISHED
        post.save(update_fields=["status", "published_at"])
        return Response(
            PostDetailSerializer(post, context={"request": request}).data
        )

    @extend_schema(responses={200: PostDetailSerializer})
    @action(detail=True, methods=["post"])
    def unpublish(self, request, pk=None):
        """Revert a published post to draft."""
        post = self.get_object()
        post.status = Post.Status.DRAFT
        post.published_at = None
        post.save(update_fields=["status", "published_at"])
        return Response(
            PostDetailSerializer(post, context={"request": request}).data
        )

    @extend_schema(responses={200: PostDetailSerializer})
    @action(detail=True, methods=["post"],
            permission_classes=[IsAuthenticated, IsAdminUser])
    def feature(self, request, pk=None):
        """Toggle the featured flag. Admin only."""
        post = self.get_object()
        post.is_featured = not post.is_featured
        post.save(update_fields=["is_featured"])
        return Response(
            PostDetailSerializer(post, context={"request": request}).data
        )

    @extend_schema(
        responses=PostListSerializer(many=True),
        parameters=[
            OpenApiParameter("status", str, description="Filter by status"),
        ],
    )
    @action(detail=False, methods=["get"],
            permission_classes=[IsAuthenticated])
    def my_posts(self, request):
        """Return the authenticated user's posts (all statuses)."""
        qs = Post.objects.filter(author=request.user).order_by("-created_at")
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(
                PostListSerializer(page, many=True, context={"request": request}).data
            )
        return Response(
            PostListSerializer(qs, many=True, context={"request": request}).data
        )


class TagViewSet(ReadOnlyModelViewSet):
    """Read-only tag list/detail. No auth required."""

    queryset         = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    search_fields    = ["name", "slug"]
    ordering         = ["name"]