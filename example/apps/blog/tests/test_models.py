"""Tests for the blog models and their business rules."""

import pytest

from apps.blog.models import Author, Post


@pytest.mark.django_db
def test_publishing_stamps_slug_and_published_at(author: Author) -> None:
    """Saving a post as published derives the slug and stamps published_at."""
    post = Post.objects.create(
        title="Olá Mundo",
        body="...",
        author=author,
        status=Post.Status.PUBLISHED,
    )
    assert post.slug == "ola-mundo"
    assert post.published_at is not None
    assert post.is_published is True


@pytest.mark.django_db
def test_draft_has_no_published_at(author: Author) -> None:
    """A draft post keeps published_at empty and is not published."""
    post = Post.objects.create(title="Draft", body="...", author=author)
    assert post.published_at is None
    assert post.is_published is False


@pytest.mark.django_db
def test_published_queryset_excludes_drafts(author: Author) -> None:
    """The published() queryset returns only published posts."""
    Post.objects.create(title="Draft", body="x", author=author)
    Post.objects.create(
        title="Live", body="x", author=author, status=Post.Status.PUBLISHED
    )
    assert Post.objects.published().count() == 1


@pytest.mark.django_db
def test_by_tag_filters_published_posts(published_post: Post) -> None:
    """The by_tag() queryset returns published posts carrying the tag."""
    from apps.blog.models import Tag

    tag = Tag.objects.create(name="django")
    published_post.tags.add(tag)
    assert Post.objects.by_tag(tag.slug).count() == 1
    assert Post.objects.by_tag("missing").count() == 0
