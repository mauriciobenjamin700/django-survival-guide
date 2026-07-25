"""Shared pytest fixtures for the blog test suite."""

from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser

from apps.blog.models import Author, Post


@pytest.fixture(autouse=True)
def _drop_whitenoise(settings: Any) -> None:
    """Remove WhiteNoise from the middleware stack for the whole suite.

    WhiteNoise scans ``STATIC_ROOT`` when it starts and warns when the folder is
    missing — and ``staticfiles/`` only exists after ``collectstatic``, which the
    tests neither need nor run. Serving static files is not under test, so the
    middleware is dropped instead of silencing the warning.

    Args:
        settings: The pytest-django fixture that restores settings afterwards.
    """
    settings.MIDDLEWARE = [m for m in settings.MIDDLEWARE if "whitenoise" not in m]


@pytest.fixture
def user(db: None) -> AbstractUser:
    """Create and return a demo authenticated user.

    Args:
        db: The pytest-django fixture enabling database access.

    Returns:
        A saved user with a known password.
    """
    return get_user_model().objects.create_user("ana", password="secret123")


@pytest.fixture
def author(user: AbstractUser) -> Author:
    """Create an author profile backed by the demo user.

    Args:
        user: The user the author profile is attached to.

    Returns:
        A saved author instance.
    """
    return Author.objects.create(user=user, display_name="Ana")


@pytest.fixture
def published_post(author: Author) -> Post:
    """Create a single published post authored by the demo author.

    Args:
        author: The author of the post.

    Returns:
        A saved, published post instance.
    """
    return Post.objects.create(
        title="Live Post",
        body="Body of a live post.",
        author=author,
        status=Post.Status.PUBLISHED,
    )
