# Reference: the model `Meta` class

!!! quote "Think like a child 🧒"
    If the model is a **toy box** and the fields are the drawers, the
    `class Meta` is the **label on the box lid**. It doesn't hold any toy at all
    — it says *how the box behaves*: what its name is, in what order the toys
    show up, and rules like "you can't have two toys with the same name."

## Use case

Your posts show up out of order, the table name came out ugly, and you want to
prevent two posts with the same title from the same author. None of that is
about *one* field — it's about the **whole table**. That's the job of `Meta`:

```python
# apps/blog/models.py
from django.db import models


class Post(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey("Author", on_delete=models.CASCADE)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-published_at"]                 # newest first
        verbose_name = "post"                          # pretty name, singular
        verbose_name_plural = "posts"                  # pretty name, plural
        constraints = [
            models.UniqueConstraint(
                fields=["author", "title"],
                name="unique_title_per_author",
            )
        ]
```

!!! info "`Meta` is a class *inside* the model"
    It doesn't inherit from anything, doesn't become a table, and has no methods
    of its own. It's just a "bulletin board" that Django reads to configure the
    model. Every option below is optional.

## Possibilities

### Ordering and names

| Option | What it does | Example |
| --- | --- | --- |
| `ordering` | Default order for queries | `["-published_at", "title"]` |
| `verbose_name` | Displayed singular name | `"article"` |
| `verbose_name_plural` | Displayed plural name | `"articles"` |
| `db_table` | Table name in the database | `"blog_posts"` |
| `db_table_comment` | Table comment in the database | `"Blog posts"` |

!!! tip "The `-` in `ordering` means descending"
    `"-published_at"` = from newest to oldest. Without the `-`, it's ascending.
    Think like a child: the `-` is the little "top-to-bottom" arrow.

!!! warning "Always set `verbose_name_plural` yourself"
    Django pluralizes by simply adding an "s". That gets irregular English words
    wrong — "person" would become "persons" instead of "people" — and any other
    language wrong entirely. Always declare the plural yourself.

### Constraints and indexes

The **modern** way (current Django) to enforce rules in the database:

```python
class Enrollment(models.Model):
    student = models.ForeignKey("Student", on_delete=models.CASCADE)
    course = models.ForeignKey("Course", on_delete=models.CASCADE)
    grade = models.IntegerField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"],
                name="unique_enrollment",
            ),
            models.CheckConstraint(
                condition=models.Q(grade__gte=0) & models.Q(grade__lte=100),
                name="grade_between_0_and_100",
            ),
        ]
        indexes = [
            models.Index(fields=["course", "-grade"], name="course_grade_idx"),
        ]
```

| Option | What it does |
| --- | --- |
| `constraints` | List of `UniqueConstraint` / `CheckConstraint` applied **in the database** |
| `indexes` | List of `Index` to speed up queries |
| `unique_together` | **Old** way of combined uniqueness (prefer `UniqueConstraint`) |
| `index_together` | **Old** way of combined indexing (prefer `indexes`) |

!!! danger "Prefer `constraints`/`indexes` over `unique_together`/`index_together`"
    The `*_together` forms still work, but they're on their way to retirement.
    `UniqueConstraint` and `Index` are more powerful (they accept conditions,
    expressions, names) and are the recommended path today.

!!! info "Constraint × form validation"
    A `constraint` lives **in the database** — it's the last line of defense,
    guaranteeing integrity even if someone inserts data outside of Django. Form
    validation is the first line (a friendly message). Use both: belt and
    suspenders.

### Abstract models: inheritance without a table

Want several models to share the same fields (e.g., `created_at`,
`updated_at`) without repeating code? Use an **abstract** model:

```python
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True     # (1)!


class Post(TimeStampedModel):      # inherits created_at and updated_at
    title = models.CharField(max_length=200)


class Comment(TimeStampedModel):   # inherits too
    body = models.TextField()
```

1. `abstract = True` says: "don't create a table for *me*; just lend my fields
   to whoever inherits." Think like a child: it's a **cake recipe**, not the
   cake. Each child bakes its own cake with the same ingredients.

| Option | What it does |
| --- | --- |
| `abstract` | `True` = recipe-model, no table of its own |
| `proxy` | `True` = same table as the parent, only changes behavior (methods, ordering) |
| `managed` | `False` = Django doesn't create/drop the table (legacy database) |

!!! tip "Where the child's `Meta` inherits from the parent's `Meta`"
    When inheriting from an abstract model, the child **inherits the parent's
    `Meta`**. If the child needs its own options but wants to keep the parent's,
    inherit explicitly:
    ```python
    class Post(TimeStampedModel):
        class Meta(TimeStampedModel.Meta):
            ordering = ["-created_at"]
    ```

### Permissions

```python
class Report(models.Model):
    class Meta:
        permissions = [
            ("can_export", "Can export reports"),
            ("can_publish", "Can publish reports"),
        ]
        default_permissions = ["add", "change", "delete", "view"]  # the default
```

| Option | What it does |
| --- | --- |
| `permissions` | **Extra** permissions beyond the four automatic ones |
| `default_permissions` | Customizes the automatic ones (`add`/`change`/`delete`/`view`) |

### Summary table of all the useful options

| Option | Category |
| --- | --- |
| `ordering` | Ordering |
| `verbose_name`, `verbose_name_plural` | Displayed names |
| `db_table`, `db_table_comment` | Table name/comment |
| `constraints` | Database constraints |
| `indexes` | Indexes |
| `unique_together`, `index_together` | (legacy — avoid) |
| `abstract` | Recipe-model with no table |
| `proxy` | Same table, different behavior |
| `managed` | Whether Django creates the table or not |
| `permissions`, `default_permissions` | Permissions |
| `get_latest_by` | Field used by `.latest()`/`.earliest()` |
| `app_label` | Which app the model belongs to (when ambiguous) |

## Recap

- `Meta` configures the **whole table**, not a field. It's a bulletin board.
- Most used: `ordering` (the `-` = descending), `verbose_name(_plural)`,
  `constraints` and `indexes` (the modern forms — avoid `*_together`).
- `abstract = True` creates a **recipe-model** to reuse fields via inheritance,
  with no table of its own; the `Meta` is inherited by the children.
- Constraints live in the database (last defense); forms give the friendly
  message (first defense). Use both.

Models mastered. Now the **[class-based views](views-cbv.md)** — attribute by
attribute, method by method.
