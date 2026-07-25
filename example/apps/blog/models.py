"""Database models for the blog.

The schema is intentionally small but covers every relationship kind you meet
in real Django projects:

* ``Author`` — a one-to-one profile extending the built-in ``User``.
* ``Tag`` — a simple lookup table reached through a many-to-many relation.
* ``Post`` — the central entity, with a foreign key to its author, a
  many-to-many to tags, an enumerated status and a custom manager.
* ``Comment`` — a foreign key back to its post (one-to-many).

Every field is explicit and every model exposes ``__str__`` and, where it maps
to a page, ``get_absolute_url`` so templates and the admin stay clean.
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

    Keeping the profile separate from ``User`` follows Django's recommended
    pattern: authentication data stays on ``User`` while blog-specific fields
    (bio, website) live here.

    Attributes:
        user (User): The auth user this profile belongs to. Reachable back as
            ``user.author_profile``; deleting the user deletes the profile.
        display_name (str): The name shown to readers, e.g. in a post byline.
        bio (str): Free-form presentation text. Empty string when unset.
        website (str): Optional personal URL, validated as a URL.
        posts (QuerySet[Post]): Reverse accessor for the author's posts, created
            by ``Post.author``'s ``related_name``.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="author_profile",
    )
    display_name = models.CharField(max_length=80)
    bio = models.TextField(blank=True)
    website = models.URLField(blank=True)

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
        slug (str): URL-safe version of ``name``, derived on save when left
            blank, so a tag reaches its page as ``/tags/django/``.
        posts (QuerySet[Post]): Reverse accessor for the tagged posts, created
            by ``Post.tags``'s ``related_name``.
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
        """Populate ``slug`` from ``name`` on first save when left blank.

        Args:
            *args: Positional arguments forwarded to ``Model.save``.
            **kwargs: Keyword arguments forwarded to ``Model.save``.
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class PostQuerySet(models.QuerySet["Post"]):
    """Custom queryset exposing reusable, chainable filters."""

    def published(self) -> "PostQuerySet":
        """Return only posts whose status is published.

        Returns:
            A queryset narrowed to published posts, ordered by the default
            model ordering.
        """
        return self.filter(status=Post.Status.PUBLISHED)

    def by_tag(self, slug: str) -> "PostQuerySet":
        """Return published posts carrying the tag identified by ``slug``.

        Args:
            slug: The slug of the tag to filter by.

        Returns:
            A queryset of matching published posts.
        """
        return self.published().filter(tags__slug=slug)


class Post(models.Model):
    """A blog post authored by an :class:`Author` and labelled with tags.

    Attributes:
        title (str): The headline, shown in listings and as the page title.
        slug (str): URL-safe version of ``title``, derived on save when blank.
            Unique, because it identifies the post in its URL.
        author (Author): The profile that wrote the post. Deleting the author
            deletes their posts.
        body (str): The post content, unbounded text.
        tags (QuerySet[Tag]): Labels attached to the post; may be empty.
        status (Status): Publication state — ``DRAFT`` or ``PUBLISHED``.
        created_at (datetime): Stamped once, at creation.
        updated_at (datetime): Refreshed on every save.
        published_at (datetime | None): Stamped the first time the post becomes
            published; ``None`` while it is a draft.
        comments (QuerySet[Comment]): Reverse accessor for reader comments,
            created by ``Comment.post``'s ``related_name``.
        objects (PostQuerySet): Manager built from :class:`PostQuerySet`, so
            ``Post.objects.published()`` works.
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
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [models.Index(fields=["-published_at"])]
        verbose_name = "Post"
        verbose_name_plural = "Posts"

    def __str__(self) -> str:
        """Return the post title."""
        return self.title

    def get_absolute_url(self) -> str:
        """Return the canonical URL of the post detail page.

        Returns:
            The path to this post's detail view, resolved from its slug.
        """
        return reverse("blog:post-detail", kwargs={"slug": self.slug})

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Derive the slug and stamp ``published_at`` when appropriate.

        The slug is generated from the title on first save. ``published_at`` is
        set the moment the post transitions into the published state and it is
        still empty.

        Args:
            *args: Positional arguments forwarded to ``Model.save``.
            **kwargs: Keyword arguments forwarded to ``Model.save``.
        """
        if not self.slug:
            self.slug = slugify(self.title)
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_published(self) -> bool:
        """Return whether the post is currently published."""
        return self.status == self.Status.PUBLISHED

    def approved_comments(self) -> QuerySet["Comment"]:
        """Return this post's approved comments, newest first.

        Returns:
            A queryset of approved comments ordered by creation time.
        """
        return self.comments.filter(is_approved=True)


class Comment(models.Model):
    """A reader comment attached to a single :class:`Post`.

    Attributes:
        post (Post): The commented post. Deleting the post deletes its comments.
        author_name (str): Name the reader typed; comments need no login.
        email (str): Reader's email, validated but never shown publicly.
        body (str): The comment text.
        is_approved (bool): Moderation flag — ``False`` until a moderator
            approves, and only approved comments are rendered.
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
