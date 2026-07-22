# Models and the ORM

A **model** is a Python class that represents a database table. Each
attribute is a column. The **ORM** (Object-Relational Mapper) translates operations on
Python objects into SQL — you work with objects, Django writes the SQL.

!!! quote "The core idea"
    You describe the data **once**, as a class. Django generates the
    tables, validates the data, and gives you an API to query it — without you writing
    SQL by hand.

## Our first model: `Tag`

Let's go from simplest to most complex. A `Tag` is just a label:

```python
from django.db import models
from django.utils.text import slugify


class Tag(models.Model):
    """A free-form label used to group related posts."""

    name = models.CharField(max_length=40, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        """Return the tag name."""
        return self.name

    def save(self, *args: object, **kwargs: object) -> None:
        """Populate ``slug`` from ``name`` on first save when left blank."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
```

Let's go piece by piece:

- **`models.Model`** — every model class inherits from it. It's what gives access to the
  ORM (`.objects`, `.save()`, etc.).
- **`CharField` / `SlugField`** — column types. `max_length` is required for
  short text; `unique=True` creates a uniqueness constraint in the database.
- **`blank=True`** — allows the field to be empty *in forms* (validation).
- **`class Meta`** — model metadata. `ordering` defines the default ordering of
  queries.
- **`__str__`** — how the object appears in the admin and the shell. Always define it.
- **overridden `save()`** — we generate the `slug` from the `name` the first time.
  We call `super().save(...)` so Django does the actual work.

!!! warning "`blank` vs `null`"
    - **`blank`** is about **form validation** (the field can be left empty).
    - **`null`** is about the **database** (the column accepts `NULL`).

    For text fields, prefer `blank=True` and do **not** use `null=True` — this way
    "empty" is always `""`, never `None`, avoiding two ways of saying "nothing".

## Relationships

This is where the power of the ORM lives. Our blog has three kinds of relationship:

=== "One-to-one (`Author` ↔ `User`)"

    ```python
    from django.conf import settings


    class Author(models.Model):
        """A public author profile attached one-to-one to an auth user."""

        user = models.OneToOneField(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name="author_profile",
        )
        display_name = models.CharField(max_length=80)
        bio = models.TextField(blank=True)
        website = models.URLField(blank=True)
    ```

    We separate the public profile (`Author`) from the auth user (`User`).
    A user has **one** profile. We access it with `user.author_profile`.

=== "Many-to-one (`Post` → `Author`)"

    ```python
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    ```

    Each post has **one** author; an author has **many** posts. The
    `related_name="posts"` creates the reverse path: `author.posts.all()`.

=== "Many-to-many (`Post` ↔ `Tag`)"

    ```python
    tags = models.ManyToManyField(Tag, related_name="posts", blank=True)
    ```

    A post has several tags; a tag marks several posts. Django creates the
    intermediate table on its own.

!!! danger "Always set `on_delete`"
    On `ForeignKey` and `OneToOneField`, `on_delete` is **required**. It says
    what to do when the referenced object is deleted:

    - `CASCADE` — also deletes those that depend on it (delete the author, the posts vanish).
    - `PROTECT` — prevents the deletion while there are dependents.
    - `SET_NULL` — clears the reference (requires `null=True`).

## The central model: `Post`

Bringing it all together, plus a **status enum** and properties:

```python
from django.urls import reverse
from django.utils import timezone


class Post(models.Model):
    """A blog post authored by an Author and labelled with tags."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="posts")
    body = models.TextField()
    tags = models.ManyToManyField(Tag, related_name="posts", blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [models.Index(fields=["-published_at"])]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        """Return the canonical URL of the post detail page."""
        return reverse("blog:post-detail", kwargs={"slug": self.slug})

    @property
    def is_published(self) -> bool:
        return self.status == self.Status.PUBLISHED
```

Highlights:

- **`TextChoices`** — the modern, typed way to define options. `Status.DRAFT`
  is worth `"draft"` and displays `"Draft"`. No loose constants or magic strings.
- **`auto_now_add`** vs **`auto_now`** — the first records the date only on creation; the
  second updates on every save.
- **`get_absolute_url`** — returns the object's URL. The admin and templates use
  this; we never write the URL "by hand".
- **`indexes`** — a database index to order by `published_at` quickly.
- **`@property is_published`** — domain logic next to the model, typed.

!!! tip "Fat model, thin view"
    Rules that depend only on the object's own data (like `is_published`)
    live in the **model**. This way the logic stays close to the data and is reusable
    across views, templates, and tests.

## Recap

- A **model** is a class that becomes a table; attributes become columns.
- Relationships: `OneToOneField`, `ForeignKey`, `ManyToManyField` — always with
  `on_delete` on the FKs.
- `related_name` creates the reverse access (`author.posts`).
- `TextChoices` gives typed enums; `__str__` and `get_absolute_url` are essential.
- Put the object's own rules in the model (`@property`, methods).

We defined the tables in code. Now we need to actually create them in the database —
that's the job of **[Migrations](migrations.md)**.
