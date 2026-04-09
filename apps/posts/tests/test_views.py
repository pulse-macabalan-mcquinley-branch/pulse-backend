"""apps/posts/tests/test_views.py"""
import pytest
from rest_framework import status

from factories import AdminFactory, PostFactory, TagFactory, UserFactory


BASE = "/api/v1/posts/"


# ─────────────────────────────────────────────────────────────
# LIST
# ─────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestPostList:

    def test_anonymous_sees_only_published(self, api_client):
        PostFactory.create_batch(3, status="published")
        PostFactory.create_batch(2, status="draft")
        response = api_client.get(BASE)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["pagination"]["count"] == 3

    def test_author_sees_own_drafts_and_all_published(self, auth_client, user):
        PostFactory(author=user, status="draft")       # own draft
        PostFactory(status="published")                # others published
        PostFactory(status="draft")                    # others draft — NOT visible
        response = auth_client.get(BASE)
        assert response.data["pagination"]["count"] == 2

    def test_admin_sees_all(self, admin_client):
        PostFactory.create_batch(3, status="published")
        PostFactory.create_batch(4, status="draft")
        response = admin_client.get(BASE)
        assert response.data["pagination"]["count"] == 7

    def test_filter_by_status(self, admin_client):
        PostFactory.create_batch(2, status="published")
        PostFactory.create_batch(3, status="draft")
        response = admin_client.get(BASE, {"status": "draft"})
        assert response.data["pagination"]["count"] == 3

    def test_filter_by_featured(self, api_client):
        PostFactory.create_batch(4, status="published", is_featured=False)
        PostFactory.create_batch(2, status="published", is_featured=True)
        response = api_client.get(BASE, {"is_featured": "true"})
        assert response.data["pagination"]["count"] == 2

    def test_search_by_title(self, api_client):
        PostFactory(title="Django REST Framework Guide", status="published")
        PostFactory(title="Completely unrelated post",   status="published")
        response = api_client.get(BASE, {"search": "Django REST"})
        assert response.data["pagination"]["count"] == 1

    def test_filter_by_tag_slug(self, api_client):
        tag     = TagFactory(slug="python")
        match   = PostFactory(status="published")
        nomatch = PostFactory(status="published")
        match.tags.add(tag)
        response = api_client.get(BASE, {"tags__slug": "python"})
        assert response.data["pagination"]["count"] == 1

    def test_ordering_by_views(self, api_client):
        PostFactory(status="published", views_count=100)
        PostFactory(status="published", views_count=500)
        PostFactory(status="published", views_count=10)
        response = api_client.get(BASE, {"ordering": "-views_count"})
        counts = [p["views_count"] for p in response.data["results"]]
        assert counts == sorted(counts, reverse=True)


# ─────────────────────────────────────────────────────────────
# CREATE
# ─────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestPostCreate:

    def test_authenticated_can_create(self, auth_client):
        payload = {
            "title" : "My New Post",
            "body"  : "This is the body of the post, enough content.",
            "status": "draft",
            "tags"  : [],
        }
        response = auth_client.post(BASE, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "My New Post"

    def test_author_set_automatically(self, auth_client, user):
        payload = {"title": "Auto Author Post", "body": "Body here.", "tags": []}
        response = auth_client.post(BASE, payload, format="json")
        assert response.data["author"]["id"] == str(user.id)

    def test_slug_auto_generated(self, auth_client):
        payload = {"title": "Slug Is Auto Generated", "body": "Body.", "tags": []}
        response = auth_client.post(BASE, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_non_admin_cannot_publish_directly(self, auth_client):
        payload = {"title": "Try publish", "body": "Body.", "tags": [],
                    "status": "published"}
        response = auth_client.post(BASE, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_admin_can_publish_directly(self, admin_client):
        payload = {"title": "Admin Publish", "body": "Body.", "tags": [],
                    "status": "published"}
        response = admin_client.post(BASE, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_anonymous_cannot_create(self, api_client):
        payload = {"title": "No auth", "body": "Body.", "tags": []}
        response = api_client.post(BASE, payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_with_tags(self, auth_client):
        tag1 = TagFactory(slug="django")
        tag2 = TagFactory(slug="api")
        payload = {"title": "Tagged Post", "body": "Body.", "tags": ["django", "api"]}
        response = auth_client.post(BASE, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED


# ─────────────────────────────────────────────────────────────
# RETRIEVE
# ─────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestPostRetrieve:

    def test_retrieve_published_anon(self, api_client):
        post = PostFactory(status="published")
        response = api_client.get(f"{BASE}{post.pk}/")
        assert response.status_code == status.HTTP_200_OK
        assert "body" in response.data   # detail serializer includes body

    def test_retrieve_increments_views(self, api_client):
        post = PostFactory(status="published", views_count=0)
        api_client.get(f"{BASE}{post.pk}/")
        post.refresh_from_db()
        assert post.views_count == 1

    def test_retrieve_own_draft(self, auth_client, user):
        post = PostFactory(author=user, status="draft")
        response = auth_client.get(f"{BASE}{post.pk}/")
        assert response.status_code == status.HTTP_200_OK

    def test_cannot_retrieve_others_draft(self, auth_client):
        other_post = PostFactory(status="draft")
        response = auth_client.get(f"{BASE}{other_post.pk}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ─────────────────────────────────────────────────────────────
# UPDATE
# ─────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestPostUpdate:

    def test_owner_can_patch(self, auth_client, user):
        post = PostFactory(author=user)
        response = auth_client.patch(
            f"{BASE}{post.pk}/",
            {"title": "Updated Title"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

    def test_non_owner_cannot_patch(self, auth_client):
        post = PostFactory(status="published")  # different author
        response = auth_client.patch(
            f"{BASE}{post.pk}/",
            {"title": "Hack"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_patch_any(self, admin_client):
        post = PostFactory(status="published")
        response = admin_client.patch(
            f"{BASE}{post.pk}/",
            {"title": "Admin Edit"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

    def test_update_tags(self, auth_client, user):
        tag = TagFactory(slug="python")
        post = PostFactory(author=user)
        response = auth_client.patch(
            f"{BASE}{post.pk}/",
            {"tags": ["python"]},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK


# ─────────────────────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestPostDelete:

    def test_owner_can_delete(self, auth_client, user):
        post = PostFactory(author=user)
        response = auth_client.delete(f"{BASE}{post.pk}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_non_owner_cannot_delete(self, auth_client):
        post = PostFactory(status="published")
        response = auth_client.delete(f"{BASE}{post.pk}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_delete_any(self, admin_client):
        post = PostFactory(status="published")
        response = admin_client.delete(f"{BASE}{post.pk}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT


# ─────────────────────────────────────────────────────────────
# CUSTOM ACTIONS
# ─────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestPostActions:

    def test_publish_action(self, auth_client, user):
        post = PostFactory(author=user, status="draft")
        response = auth_client.post(f"{BASE}{post.pk}/publish/")
        assert response.status_code == status.HTTP_200_OK
        post.refresh_from_db()
        assert post.status == "published"
        assert post.published_at is not None

    def test_cannot_publish_already_published(self, auth_client, user):
        post = PostFactory(author=user, status="published")
        response = auth_client.post(f"{BASE}{post.pk}/publish/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unpublish_action(self, auth_client, user):
        post = PostFactory(author=user, status="published")
        response = auth_client.post(f"{BASE}{post.pk}/unpublish/")
        assert response.status_code == status.HTTP_200_OK
        post.refresh_from_db()
        assert post.status == "draft"

    def test_feature_requires_admin(self, auth_client, user):
        post = PostFactory(author=user, status="published")
        response = auth_client.post(f"{BASE}{post.pk}/feature/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_feature(self, admin_client):
        post = PostFactory(status="published", is_featured=False)
        response = admin_client.post(f"{BASE}{post.pk}/feature/")
        assert response.status_code == status.HTTP_200_OK
        post.refresh_from_db()
        assert post.is_featured is True

    def test_my_posts_returns_own_only(self, auth_client, user):
        PostFactory.create_batch(3, author=user)
        PostFactory.create_batch(2, status="published")  # others
        response = auth_client.get(f"{BASE}my-posts/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["pagination"]["count"] == 3

    def test_my_posts_filter_by_status(self, auth_client, user):
        PostFactory(author=user, status="draft")
        PostFactory(author=user, status="published")
        response = auth_client.get(f"{BASE}my-posts/", {"status": "draft"})
        assert response.data["pagination"]["count"] == 1