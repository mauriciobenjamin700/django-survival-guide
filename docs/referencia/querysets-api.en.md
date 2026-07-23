# Reference: the full QuerySet API

!!! quote "Think like a child 🧒"
    Imagine a **giant box of marbles** (all the records). A **QuerySet** is a
    request: "give me only the blue marbles, in order of size". The trick: as long
    as you're just describing the request, nobody opens the box. Only when you
    **grab** the marbles to play with them (iterate, count, list) does Django open
    the box **once** and bring everything. This is called *laziness*.

## Use case

You want an author's published posts, newest first, already bringing the author
along so you don't run a thousand queries:

```python
posts = (
    Post.objects
    .filter(status="published", author__display_name="Ana")
    .order_by("-published_at")
    .select_related("author")
)
# No query yet — just the description of the request.

for post in posts:            # HERE the box opens, once
    print(post.title)
```

Now the full catalog of methods: which ones return **another QuerySet** (so you
can chain) and which ones return a **final value** (the box opens).

## Possibilities

### Methods that return a QuerySet (chainable, lazy)

| Method | What it does |
| --- | --- |
| `all()` | A copy of everything |
| `filter(**kw)` | Keeps the ones that match |
| `exclude(**kw)` | Removes the ones that match |
| `order_by(*fields)` | Sorts (`-` = descending) |
| `reverse()` | Reverses the order |
| `distinct()` | Removes duplicates |
| `values(*fields)` | Dicts instead of objects |
| `values_list(*fields)` | Tuples (or `flat=True` for a simple list) |
| `annotate(...)` | Adds a computed field per row |
| `select_related(*fk)` | JOIN for FK/OneToOne (against N+1) |
| `prefetch_related(*rel)` | Matched fetch for M2M/reverse |
| `only(*fields)` / `defer(*fields)` | Loads/defers columns |
| `none()` | Empty QuerySet |
| `union/intersection/difference` | Set operations |

### Methods that return a value (the box opens here)

| Method | Returns |
| --- | --- |
| `get(**kw)` | **One** object (or a `DoesNotExist`/`MultipleObjectsReturned` error) |
| `first()` / `last()` | One object or `None` |
| `count()` | A count (`SELECT COUNT(*)`) |
| `exists()` | `True`/`False` (is there any?) |
| `aggregate(...)` | Dict with totals (sum, average...) |
| `latest(field)` / `earliest(field)` | The newest/oldest |
| `in_bulk(ids)` | Dict `{id: object}` |
| `create(**kw)` | Creates and saves, returns the object |
| `get_or_create(**kw)` | `(object, created?)` |
| `update_or_create(**kw)` | `(object, created?)`, updating if it exists |
| `bulk_create([...])` | Inserts several in one query |
| `update(**kw)` | Bulk update, returns number of rows |
| `delete()` | Deletes, returns a count |

!!! danger "`get()` raises an exception; `filter().first()` doesn't"
    - `get()` expects **exactly one**. Zero → `DoesNotExist`; more than one →
      `MultipleObjectsReturned`.
    - For "maybe it exists", use `filter(...).first()` (gives `None`) or
      `get_object_or_404(...)` in the views.

### Lookups: the `__` that filters finely

Think like a child: the `__` is the magnifier that looks *inside* the field.

| Lookup | Meaning | Example |
| --- | --- | --- |
| `exact` / `iexact` | Equal / equal ignoring case | `title__iexact="olá"` |
| `contains` / `icontains` | Contains / ignoring case | `title__icontains="django"` |
| `startswith` / `endswith` | Starts/ends with | `slug__startswith="2026"` |
| `in` | Is in the list | `id__in=[1, 2, 3]` |
| `gt` / `gte` / `lt` / `lte` | Greater/less (or equal) | `views__gte=100` |
| `range` | Between two values | `published_at__range=(a, b)` |
| `isnull` | Is null? | `published_at__isnull=True` |
| `date` / `year` / `month` / `day` | Parts of a date | `created_at__year=2026` |
| `regex` / `iregex` | Matches regex | `title__regex=r"^\d"` |

```python
Post.objects.filter(title__icontains="orm", created_at__year=2026)
Post.objects.filter(author__user__email__endswith="@empresa.com")   # crosses relations
```

### Crossing relations

```python
# posts whose tag has slug "django"
Post.objects.filter(tags__slug="django")

# reverse access: comments of published posts
Comment.objects.filter(post__status="published")
```

### `F`: compare/update using the database itself

Think like a child: `F` is pointing to **another drawer** of the same record,
without taking the value out.

```python
from django.db.models import F

# increment without a race condition (all in the database, one query)
Post.objects.filter(pk=1).update(views=F("views") + 1)

# posts with more likes than comments
Post.objects.filter(likes__gt=F("comments_count"))
```

### `Q`: OR, AND, NOT

Think like a child: `filter(a=1, b=2)` is always "**and**". When you want "**or**",
you call `Q`.

```python
from django.db.models import Q

# title contains "django" OR body contains "python"
Post.objects.filter(Q(title__icontains="django") | Q(body__icontains="python"))

# published AND NOT featured
Post.objects.filter(Q(status="published") & ~Q(is_featured=True))
```

| Operator | Meaning |
| --- | --- |
| `\|` | OR |
| `&` | AND |
| `~` | NOT |

### `annotate` and `aggregate`: computations

- **`aggregate`** → one result for the **whole set** (a dict).
- **`annotate`** → one result **per row** (becomes an extra field).

```python
from django.db.models import Avg, Count, Sum

# overall total (aggregate)
Post.objects.aggregate(total=Count("id"), media_views=Avg("views"))
# -> {"total": 42, "media_views": 137.5}

# per row (annotate): each post with its number of comments
posts = Post.objects.annotate(n_comments=Count("comments")).order_by("-n_comments")
for p in posts:
    print(p.title, p.n_comments)
```

| Function | Computes |
| --- | --- |
| `Count` | A count |
| `Sum` | A sum |
| `Avg` | An average |
| `Max` / `Min` | Maximum / minimum |

### Fighting N+1 (again, because it's what hurts the most)

```python
# FK / OneToOne -> select_related (does a JOIN)
Post.objects.select_related("author")

# M2M / reverse -> prefetch_related (2 matched queries)
Post.objects.prefetch_related("tags", "comments")
```

!!! danger "Golden rule"
    Going to iterate and access a relation? **FK/OneToOne → `select_related`**;
    **M2M/reverse → `prefetch_related`**. Without it, 100 objects turn into 101
    queries.

!!! quote "📖 In the official docs"
    - [QuerySet API reference](https://docs.djangoproject.com/en/stable/ref/models/querysets/)
    - [Making queries](https://docs.djangoproject.com/en/stable/topics/db/queries/)

## Recap

- QuerySets are **lazy**: they only hit the database when you use the data.
- Chainable (`filter`, `exclude`, `order_by`, `annotate`, `select_related`) ×
  final (`get`, `first`, `count`, `exists`, `aggregate`, `update`).
- `get()` raises an exception; `filter().first()` returns `None`.
- Lookups with `__` (`icontains`, `gte`, `in`, `year`, `isnull`) cross relations.
- `F` compares/updates inside the database; `Q` does OR/AND/NOT.
- `aggregate` (the set) × `annotate` (per row). And always take care of N+1.

All of this depends on configuration. See the map in **[settings](settings.md)**.
