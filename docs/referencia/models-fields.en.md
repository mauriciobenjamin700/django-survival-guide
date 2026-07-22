# Reference: model fields

!!! quote "Think like a child 🧒"
    A **model** is an organizer box. Each **field** is a little drawer of that
    box: one holds *names*, another holds *numbers*, another holds *dates*. When
    you say "this drawer only fits text up to 200 letters," Django won't let
    anyone stuff the wrong thing in there. The **fields** are the rules of each
    drawer.

## Use case

You want to store blog posts. Each post has a title (short text), a body (long
text), a date, and a status. You describe this **once**, as a class, and Django
creates the table and validates the data:

```python
# apps/blog/models.py
from django.db import models


class Post(models.Model):
    """A single blog post."""

    title = models.CharField(max_length=200)
    body = models.TextField()
    published_at = models.DateTimeField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
```

There you go: four drawers, each with its own rule. Now let's look at **all the
possible drawers** and **all the adjustment knobs** of each one.

## Possibilities

### Options common to (almost) all fields

These knobs exist on virtually any field. They're what confuses people the most
in the official docs — here, one at a time.

| Option | What it does | Default |
| --- | --- | --- |
| `null` | The column accepts `NULL` in the **database** | `False` |
| `blank` | The field can be left empty during **form validation** | `False` |
| `default` | Value used when nothing is provided (value or callable) | — |
| `unique` | No other record can have the same value | `False` |
| `db_index` | Creates an index on the column (faster lookups) | `False` |
| `primary_key` | Makes this field the primary key | `False` |
| `editable` | If `False`, disappears from forms and the admin | `True` |
| `choices` | Restricts to a list of options | — |
| `validators` | List of functions that validate the value | `[]` |
| `verbose_name` | The "pretty" name shown to the user | field name |
| `help_text` | Little help text on the form | `""` |
| `error_messages` | Customizes the error messages | — |
| `db_column` | Column name in the database (if different from the attribute) | attribute name |
| `db_comment` | Comment on the column, stored in the database | — |

!!! danger "`null` × `blank`: Django's #1 confusion"
    - **`null`** is about the **database**: the column accepts "nothing" (`NULL`).
    - **`blank`** is about **forms**: the user can leave it empty.

    Think like a child: `null` is "the drawer can be *physically* empty";
    `blank` is "the grown-up *allows* you not to fill it in."

    Rule of thumb: for **text** (`CharField`, `TextField`), use only
    `blank=True` and **never** `null=True` — that way "empty" is always `""`, and
    you don't have two ways of saying "nothing" (`""` and `None`). For numbers,
    dates, and relations, `null=True` does make sense when the value is optional.

#### `default`: value or function

```python
from django.utils import timezone

class Post(models.Model):
    created_at = models.DateTimeField(default=timezone.now)  # (1)!
    views = models.IntegerField(default=0)
    tags_cache = models.JSONField(default=list)              # (2)!
```

1. Pass the **function** (`timezone.now`), without parentheses. Django calls it
   at creation time. If you wrote `timezone.now()`, the value would be frozen at
   the moment the server started. 😱
2. For lists/dicts as a default, pass the **callable** (`list`, `dict`), never a
   literal `[]` or `{}` — otherwise every record would share the same object.

#### `choices`: the modern way with `TextChoices`

```python
class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"        # (value in the database, displayed label)
        PUBLISHED = "published", "Published"

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )
```

!!! tip "Why `TextChoices` and not a loose list"
    `Status.PUBLISHED` is readable, typed, and auto-completable. And Django gives
    you a `post.get_status_display()` method for free that returns the pretty
    label (`"Published"`). Never scatter magic strings (`"published"`) throughout
    your code.

### Text fields

| Field | Holds | Key option |
| --- | --- | --- |
| `CharField` | Short text | `max_length` (required) |
| `TextField` | Long text | — |
| `SlugField` | URL-friendly text (letters, numbers, hyphen) | `max_length`, `allow_unicode` |
| `EmailField` | Email (validates the format) | `max_length` |
| `URLField` | URL (validates the format) | `max_length` |
| `UUIDField` | UUID | usually comes with `default=uuid.uuid4` |

```python
import uuid

class Article(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    body = models.TextField(blank=True)
    contact = models.EmailField(blank=True)
```

### Numeric fields

| Field | Holds |
| --- | --- |
| `IntegerField` | Integer |
| `BigIntegerField` | Large integer (64 bits) |
| `PositiveIntegerField` | Integer ≥ 0 |
| `SmallIntegerField` | Small integer |
| `FloatField` | Floating point |
| `DecimalField` | Exact decimal (money!) — requires `max_digits` and `decimal_places` |

```python
class Product(models.Model):
    stock = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=8, decimal_places=2)  # up to 999999.99
```

!!! warning "Money is `DecimalField`, never `FloatField`"
    `FloatField` has rounding errors (`0.1 + 0.2 != 0.3`). For price, balance,
    any monetary value: `DecimalField`. `max_digits` is the total number of
    digits; `decimal_places` is how many come after the decimal point.

### Date and time fields

| Field | Holds | Special options |
| --- | --- | --- |
| `DateField` | Date only | `auto_now`, `auto_now_add` |
| `DateTimeField` | Date + time | `auto_now`, `auto_now_add` |
| `TimeField` | Time only | `auto_now`, `auto_now_add` |
| `DurationField` | A time interval | — |

```python
class Post(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)  # stamps only on create
    updated_at = models.DateTimeField(auto_now=True)      # updates on every save
```

!!! info "`auto_now_add` × `auto_now`"
    - **`auto_now_add=True`**: stamps the date **once**, at creation. Never
      changes again. (Good for `created_at`.)
    - **`auto_now=True`**: updates **every time** you save. (Good for
      `updated_at`.)

    Think like a child: `auto_now_add` is the birth date (it never changes);
    `auto_now` is "the last time someone played with the toy."

### Boolean fields

```python
class Post(models.Model):
    is_published = models.BooleanField(default=False)
    reviewed = models.BooleanField(null=True)  # 3 states: yes / no / don't-know-yet
```

### File fields

| Field | Holds | Requires |
| --- | --- | --- |
| `FileField` | Path of an uploaded file | `upload_to`, `MEDIA_ROOT` configured |
| `ImageField` | Same, but validates that it's an image | `Pillow` installed |

```python
class Profile(models.Model):
    avatar = models.ImageField(upload_to="avatars/%Y/%m/", blank=True)
```

### Relationship fields

The heart of the ORM. Detailed in [Models and the ORM](../tutorial/models.md);
here's the summary of options:

| Field | Relationship | Main options |
| --- | --- | --- |
| `ForeignKey` | Many-to-one | `on_delete` (required), `related_name`, `related_query_name`, `limit_choices_to` |
| `OneToOneField` | One-to-one | `on_delete` (required), `related_name` |
| `ManyToManyField` | Many-to-many | `related_name`, `through`, `symmetrical`, `blank` |

```python
class Post(models.Model):
    author = models.ForeignKey(
        "Author",
        on_delete=models.CASCADE,     # what to do if the author is deleted
        related_name="posts",         # author.posts.all()
        limit_choices_to={"is_active": True},  # only active authors in the dropdown
    )
    tags = models.ManyToManyField("Tag", related_name="posts", blank=True)
```

Values for `on_delete`:

| Value | When the referenced object is deleted... |
| --- | --- |
| `CASCADE` | Deletes the dependents along with it |
| `PROTECT` | Blocks the deletion (raises an error) |
| `RESTRICT` | Blocks it, but allows it if another cascade relation handles it |
| `SET_NULL` | Clears the reference (requires `null=True`) |
| `SET_DEFAULT` | Reverts to the `default` |
| `SET(value)` | Sets a specific value/callable |
| `DO_NOTHING` | Does nothing (careful: it can break integrity) |

!!! danger "`on_delete` is required on `ForeignKey`/`OneToOneField`"
    Without it, Django won't even let you create the model. Always ask yourself:
    "if the parent disappears, what happens to the child?"

## Recap

- A **field** is a drawer with rules. `CharField`, `IntegerField`,
  `DateTimeField`, `ForeignKey`... each type holds one thing.
- Common options: `null` (database) × `blank` (form), `default` (pass a
  *callable*, not a literal), `unique`, `db_index`, `choices` (use `TextChoices`),
  `verbose_name`, `help_text`.
- Empty text: only `blank=True`. Money: `DecimalField`. Automatic dates:
  `auto_now_add` (creation) × `auto_now` (every save).
- Relations require `on_delete` and gain a `related_name` for reverse access.

With the drawers defined, you tune the behavior of the **whole box** in the
[model Meta](models-meta.md).
