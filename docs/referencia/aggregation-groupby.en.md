# Reference: aggregation and "group by"

!!! quote "Think like a child 🧒"
    Imagine a box of colored marbles. **Aggregating** is answering summary
    questions: "how many marbles in total?", "what's the average size?". **Group
    by** is doing that count **per color**: "how many blue, how many red". Django
    makes the database compute it — you don't count by hand.

## Use case

How many posts each author has, and the average number of comments per post — in
one query, without bringing anything into Python:

```python
from django.db.models import Avg, Count

# per author (group by)
authors = Author.objects.annotate(n_posts=Count("posts"))
for a in authors:
    print(a.display_name, a.n_posts)

# overall summary
summary = Post.objects.aggregate(total=Count("id"), avg=Avg("views"))
# -> {"total": 42, "avg": 137.5}
```

## What's possible

### `aggregate` vs `annotate`: the difference that confuses

Think like a child:

- **`aggregate`** = one answer for the **whole box** (a dictionary).
- **`annotate`** = one answer for **each marble/group** (becomes an extra column).

```python
# aggregate: ONE number for all posts
Post.objects.aggregate(total=Count("id"))         # {"total": 42}

# annotate: one number PER author
Author.objects.annotate(n=Count("posts"))          # each author gets .n
```

| | `aggregate` | `annotate` |
| --- | --- | --- |
| Returns | A `dict` | A queryset |
| Granularity | The whole set | Per row/group |
| Chains? | No (it's terminal) | Yes |

### The aggregation functions

| Function | Computes |
| --- | --- |
| `Count` | Quantity |
| `Sum` | Sum |
| `Avg` | Average |
| `Max` / `Min` | Maximum / minimum |
| `StdDev` / `Variance` | Standard deviation / variance |

### How the "group by" actually happens

Think like a child: the "per color" appears when you say **which field to group
by**. In Django, that comes from `values()` before the `annotate()`:

```python
# how many posts PER status  (group by status)
(
    Post.objects
    .values("status")                    # (1)!  <- defines the group
    .annotate(n=Count("id"))             # (2)!  <- the count per group
    .order_by("-n")
)
# -> [{"status": "published", "n": 30}, {"status": "draft", "n": 12}]
```

1. `values("status")` says "group by status".
2. `annotate` computes within each group.

!!! danger "ORDER matters: `values()` BEFORE `annotate()`"
    - `values("field").annotate(...)` → **group by field** (one row per value).
    - `annotate(...).values("field")` → annotates **per row** and then picks the
      columns (does NOT group).

    Swapping the order completely changes the result. For "group by", `values`
    **first**.

### Conditional aggregation (count only what matches)

```python
from django.db.models import Count, Q

Author.objects.annotate(
    total=Count("posts"),
    published=Count("posts", filter=Q(posts__status="published")),
)
```

The `filter=Q(...)` counts only the rows that match — two numbers in the same
query.

### Careful: aggregating across multiple relations

!!! warning "Inflated counts when joining two relations"
    `Author.objects.annotate(n_posts=Count("posts"), n_comments=Count("comments"))`
    can **inflate** the numbers: the JOIN multiplies rows (each post crosses with
    each comment). The fix is `distinct=True`:
    ```python
    Count("posts", distinct=True)
    ```
    Symptom: numbers "too big" when you aggregate two relations at once.

### Filter by an aggregation result: use `filter` after the `annotate`

Think like a child: it's SQL's "HAVING". Filter **after** annotating:

```python
# authors with more than 5 posts
Author.objects.annotate(n=Count("posts")).filter(n__gt=5)
```

- `filter()` **before** the `annotate()` → filters the rows that go into the count.
- `filter()` **after** → filters by the already-counted groups (the "HAVING").

### `values_list` for lean results

```python
# list of (status, count)
Post.objects.values("status").annotate(n=Count("id")).values_list("status", "n")
# -> [("published", 30), ("draft", 12)]
```

## Recap

- `aggregate` = a summary of the set (dict); `annotate` = a column per row/group
  (queryset).
- "Group by" = `values("field")` **before** `annotate()` — the order is the
  secret.
- Conditional aggregation with `Count(..., filter=Q(...))`.
- Aggregated two relations and the number inflated? Use `distinct=True`.
- Filtering by a total is `annotate(...).filter(...)` (the "HAVING").

Files uploaded by users need a place to live: the **[storages](storages.md)**.
