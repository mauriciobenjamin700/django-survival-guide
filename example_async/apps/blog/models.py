"""Database models for the async blog.

The models are identical to the sync example — models describe the schema, and
that does not change between sync and async. What changes is *how you access*
them (``aget``, ``async for``, ``acreate``), which lives in the views.
"""

from typing import Any

from django.conf import settings
from django.db import models
from django.db.models import QuerySet
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Author(models.Model):
    """A public author profile attached one-to-one to an auth user.

    Attributes:
        user (User): The auth user this profile belongs to, reachable back as
            ``user.author_profile``.
        display_name (str): The name shown to readers.
        bio (str): Free-form presentation text. Empty string when unset.
        posts (QuerySet[Post]): Reverse accessor for the author's posts.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="author_profile",
    )
    display_name = models.CharField(max_length=80)
    bio = models.TextField(blank=True)

    class Meta:
        ordering = ["display_name"]
        verbose_name = "Author"
        verbose_name_plural = "Authors"

    def __str__(self) -> str:
        """Return the author's public display name."""
        return self.display_name


class Tag(models.Model):
    """A free-form label used to group related posts.

    Attributes:
        name (str): The label as a human types it, unique across tags.
        slug (str): URL-safe version of ``name``, derived on save when blank.
        posts (QuerySet[Post]): Reverse accessor for the tagged posts.
    """

    name = models.CharField(max_length=40, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self) -> str:
        """Return the tag name."""
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Populate the slug from the name on first save when left blank."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class PostQuerySet(models.QuerySet["Post"]):
    """Custom queryset exposing reusable, chainable filters."""

    def published(self) -> "PostQuerySet":
        """Return only posts whose status is published."""
        return self.filter(status=Post.Status.PUBLISHED)


class Post(models.Model):
    """A blog post authored by an Author and labelled with tags.

    Attributes:
        title (str): The headline shown in listings and as the page title.
        slug (str): URL-safe version of ``title``, derived on save when blank.
        author (Author): The profile that wrote the post.
        body (str): The post content.
        tags (QuerySet[Tag]): Labels attached to the post; may be empty.
        status (Status): Publication state — ``DRAFT`` or ``PUBLISHED``.
        created_at (datetime): Stamped once, at creation.
        updated_at (datetime): Refreshed on every save.
        published_at (datetime | None): Stamped when the post is first published.
        comments (QuerySet[Comment]): Reverse accessor for reader comments.
        objects (PostQuerySet): Manager built from :class:`PostQuerySet`.
    """

    class Status(models.TextChoices):
        """Publication state of a post."""

        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    body = models.TextField()
    tags = models.ManyToManyField(Tag, related_name="posts", blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name = "Post"
        verbose_name_plural = "Posts"

    def __str__(self) -> str:
        """Return the post title."""
        return self.title

    def get_absolute_url(self) -> str:
        """Return the canonical URL of the post detail page."""
        return reverse("blog:post-detail", kwargs={"slug": self.slug})

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Derive the slug and stamp ``published_at`` when appropriate."""
        if not self.slug:
            self.slug = slugify(self.title)
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def approved_comments(self) -> QuerySet["Comment"]:
        """Return this post's approved comments, newest first."""
        return self.comments.filter(is_approved=True)


class Comment(models.Model):
    """A reader comment attached to a single Post.

    Attributes:
        post (Post): The commented post.
        author_name (str): Name the reader typed; comments need no login.
        email (str): Reader's email, validated but never shown publicly.
        body (str): The comment text.
        is_approved (bool): Moderation flag; only approved comments render.
        created_at (datetime): Stamped once, at creation.
    """

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author_name = models.CharField(max_length=80)
    email = models.EmailField()
    body = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Comment"
        verbose_name_plural = "Comments"

    def __str__(self) -> str:
        """Return a short label identifying the comment and its post."""
        return f"{self.author_name} on {self.post}"
