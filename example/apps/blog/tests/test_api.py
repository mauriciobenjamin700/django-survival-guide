"""Tests for the DRF API layer."""

import pytest
from django.contrib.auth.models import AbstractUser
from rest_framework.test import APIClient

from apps.blog.models import Post


@pytest.mark.django_db
def test_api_list_is_public(published_post: Post) -> None:
    """Anonymous clients can list published posts, with pagination."""
    response = APIClient().get("/api/posts/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["results"][0]["title"] == published_post.title


@pytest.mark.django_db
def test_api_hides_drafts_from_anonymous(author) -> None:
    """Draft posts are not exposed to anonymous clients."""
    Post.objects.create(title="Draft", body="x", author=author)
    response = APIClient().get("/api/posts/")
    assert response.status_code == 200
    assert response.json()["count"] == 0


@pytest.mark.django_db
def test_api_create_requires_auth() -> None:
    """Anonymous clients cannot create posts."""
    response = APIClient().post("/api/posts/", {"title": "X", "body": "Y"})
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_api_authenticated_user_creates_post(user: AbstractUser, author) -> None:
    """An authenticated author can create a post through the API."""
    client = APIClient()
    client.force_authenticate(user=user)
    response = client.post(
        "/api/posts/",
        {"title": "Via API", "body": "Created through DRF.", "status": "published"},
        format="json",
    )
    assert response.status_code == 201
    assert Post.objects.filter(title="Via API").exists()
