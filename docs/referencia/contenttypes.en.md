# Reference: content types and generic relations

!!! quote "Think like a child 🧒"
    A normal comment sticks to **one** kind of thing (a post). But what if you
    wanted a "like" that sticks to **anything** — a post, a photo, a comment? A
    generic relation is a **universal sticky tape**: instead of pointing at a
    specific drawer, it writes down "what kind of thing" + "which id" and sticks to
    any model.

## Use case

You want a `Like` model that works for posts **and** comments **and** whatever
comes in the future — without a FK for each type. The generic relation solves it:

```python
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Like(models.Model):
    """A 'like' that can point at any model instance."""

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)  # (1)!
    object_id = models.PositiveIntegerField()                                # (2)!
    target = GenericForeignKey("content_type", "object_id")                  # (3)!
    created_at = models.DateTimeField(auto_now_add=True)
```

1. **Which type** of object (Post? Comment?).
2. **Which id** of that type.
3. The shortcut that joins the two into a natural access: `like.target`.

```python
post = Post.objects.get(pk=1)
Like.objects.create(target=post)      # liked a post
like.target                            # gives the Post back
```

## What's possible

### What the `ContentType` is

Think like a child: Django keeps a **list of all the project's models**, each with
a number. `ContentType` is that table of "kinds of thing".

```python
from django.contrib.contenttypes.models import ContentType

ct = ContentType.objects.get_for_model(Post)
ct.app_label      # "blog"
ct.model          # "post"
ct.model_class()  # <class 'apps.blog.models.Post'>
```

### The three pieces of a `GenericForeignKey`

| Piece | Stores |
| --- | --- |
| `content_type` (FK to `ContentType`) | *Which model* |
| `object_id` (integer) | *Which row* of that model |
| `GenericForeignKey(...)` | The shortcut that resolves the two into one object |

!!! info "You need the `contenttypes` app"
    `django.contrib.contenttypes` already comes in `INSTALLED_APPS` from
    `startproject` — it's a dependency of the permissions system and the admin.
    Nothing to install.

### The way back: `GenericRelation`

The `GenericForeignKey` takes you from the `Like` to the target. To go from the
**target** to the likes (`post.likes.all()`), the target model declares a
`GenericRelation`:

```python
from django.contrib.contenttypes.fields import GenericRelation


class Post(models.Model):
    likes = GenericRelation(Like, related_query_name="post")

# now the reverse path and filtering work
post.likes.count()
Post.objects.filter(likes__isnull=False)     # posts that have likes
```

### Recommended index

!!! tip "Index the pair (content_type, object_id)"
    Generic queries almost always filter by both fields together. A combined index
    speeds it up a lot:
    ```python
    class Like(models.Model):
        # ... fields ...
        class Meta:
            indexes = [models.Index(fields=["content_type", "object_id"])]
    ```

### When NOT to use a generic relation

!!! danger "Generic costs: no integrity and no clean JOIN"
    The universal tape is flexible, but it pays a price:

    - **No real foreign key** → the database doesn't guarantee that the `object_id`
      exists (no automatic `CASCADE`/`PROTECT`).
    - **Heavier queries** → you can't do a direct `JOIN`; filtering/ordering by the
      target is a pain.

    If you have **few** known target types (just Post and Comment), it's often
    better to use **two normal FKs** (with `null=True` and a `CheckConstraint`
    ensuring exactly one is filled). Use a generic relation when the set of targets
    is **open/unknown** (likes, tags, comments, attachments, audit logs).

### Who uses it under the hood

Django itself uses `contenttypes` internally: the **permissions** system
(`Permission` points at a `ContentType`) and the admin's `LogEntry` (which records
actions on any model). Libraries like `django-taggit` and generic comment systems
do too.

!!! quote "📖 In the official docs"
    - [The contenttypes framework](https://docs.djangoproject.com/en/stable/ref/contrib/contenttypes/)

## Recap

- `ContentType` is the table of "all the models"; `get_for_model(X)` gives you the
  type.
- Generic relation = `content_type` + `object_id` + `GenericForeignKey` → points
  at **any** model (`like.target`).
- `GenericRelation` on the target gives the reverse path (`post.likes`) and allows
  filtering.
- Index `(content_type, object_id)`.
- Cost: no referential integrity and no clean JOIN. Few targets → prefer normal
  FKs; open targets → generic relation.

Lots of data calls for counts per group. See
**[aggregation and group by](aggregation-groupby.md)**.
