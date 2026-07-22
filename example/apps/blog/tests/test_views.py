"""Tests for the blog's class-based views."""

import pytest
from django.contrib.auth.models import AbstractUser
from django.test import Client

from apps.blog.models import Comment, Post


@pytest.mark.django_db
def test_post_list_returns_200(client: Client, published_post: Post) -> None:
    """The post list page renders and shows published posts."""
    response = client.get("/")
    assert response.status_code == 200
    assert published_post.title.encode() in response.content


@pytest.mark.django_db
def test_post_detail_returns_200(client: Client, published_post: Post) -> None:
    """The detail page of a published post renders successfully."""
    response = client.get(published_post.get_absolute_url())
    assert response.status_code == 200


@pytest.mark.django_db
def test_draft_detail_returns_404(client: Client, author) -> None:
    """A draft post is not reachable by the public detail view."""
    draft = Post.objects.create(title="Secret", body="x", author=author)
    response = client.get(f"/posts/{draft.slug}/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_create_view_requires_login(client: Client) -> None:
    """Anonymous users are redirected to the login page."""
    response = client.get("/posts/new/")
    assert response.status_code == 302
    assert "/login/" in response["Location"]


@pytest.mark.django_db
def test_authenticated_user_can_open_create_view(
    client: Client, user: AbstractUser, author
) -> None:
    """A logged-in author can open the create form."""
    client.force_login(user)
    response = client.get("/posts/new/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_comment_submission_redirects_and_awaits_moderation(
    client: Client, published_post: Post
) -> None:
    """Posting a comment redirects back and leaves it unapproved."""
    response = client.post(
        f"/posts/{published_post.slug}/comment/",
        {"author_name": "Reader", "email": "r@example.com", "body": "Nice post!"},
    )
    assert response.status_code == 302
    assert response["Location"] == published_post.get_absolute_url()
    comment = Comment.objects.get()
    assert comment.is_approved is False
