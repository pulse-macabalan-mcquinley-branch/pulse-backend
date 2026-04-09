"""apps/posts/urls.py"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PostViewSet, TagViewSet

router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="posts")
router.register(r"tags",  TagViewSet,  basename="tags")

urlpatterns = [
    path("", include(router.urls)),
]

# ── Add to config/urls.py ─────────────────────────────────────
# path("api/v1/", include("apps.posts.urls")),

# Generated endpoints:
#
# GET    /api/v1/posts/                   PostViewSet.list
# POST   /api/v1/posts/                   PostViewSet.create
# GET    /api/v1/posts/{id}/              PostViewSet.retrieve
# PUT    /api/v1/posts/{id}/              PostViewSet.update
# PATCH  /api/v1/posts/{id}/              PostViewSet.partial_update
# DELETE /api/v1/posts/{id}/              PostViewSet.destroy
# POST   /api/v1/posts/{id}/publish/      PostViewSet.publish
# POST   /api/v1/posts/{id}/unpublish/    PostViewSet.unpublish
# POST   /api/v1/posts/{id}/feature/      PostViewSet.feature (admin)
# GET    /api/v1/posts/my-posts/          PostViewSet.my_posts
# GET    /api/v1/tags/                    TagViewSet.list
# GET    /api/v1/tags/{id}/               TagViewSet.retrieve
#
# Query parameters (list):
#   ?search=django          full-text search (title, body, tags, author)
#   ?status=published       filter by status
#   ?is_featured=true       featured only
#   ?author=<uuid>          filter by author
#   ?tags__slug=python      filter by tag slug
#   ?ordering=-views_count  sort by views (desc)
#   ?page=2&page_size=10    pagination