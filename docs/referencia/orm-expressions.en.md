# Reference: Advanced ORM (expressions)

!!! quote "Think like a child 🧒"
    You already know how to ask for marbles by color (`filter`). Now imagine
    asking for **finished** calculations: "tell me, for each box, how many blue
    marbles it has, and mark boxes with more than 10 as 'full'". Instead of
    bringing everything over and counting in Python, you ask the **database** to
    do the math — it's fast at that. *Expressions* are the language for asking for
    those calculations.

## Use case

You want, in a single query, each post with its number of comments and a
"popular/normal" label — without bringing anything into Python and counting by
hand:

```python
from django.db.models import Case, Count, Value, When

posts = (
    Post.objects
    .annotate(n_comments=Count("comments"))
    .annotate(
        label=Case(
            When(n_comments__gte=10, then=Value("popular")),
            default=Value("normal"),
        )
    )
)
for p in posts:
    print(p.title, p.n_comments, p.label)   # it all came ready from the database
```

## Possibilities

### `Case`/`When`: the database's "if/else"

Think like a child: a line of "if... then..." questions, with an "otherwise" at
the end.

```python
from django.db.models import Case, When, Value, IntegerField

Post.objects.annotate(
    priority=Case(
        When(status="published", then=Value(1)),
        When(status="draft", then=Value(2)),
        default=Value(9),
        output_field=IntegerField(),
    )
).order_by("priority")
```

!!! tip "`output_field` when the type is ambiguous"
    If Django can't infer the result type (mixing types), pass
    `output_field=IntegerField()` (or `CharField`, etc.) so it won't complain.

### Conditional aggregation: count only what matches

```python
from django.db.models import Count, Q

Author.objects.annotate(
    total=Count("posts"),
    publicados=Count("posts", filter=Q(posts__status="published")),
)
```

The `filter=Q(...)` inside `Count` counts **only** the rows that match — two
different numbers in the same query.

### `Subquery` and `OuterRef`: one query inside another

Think like a child: for each box, you ask one extra little question — "what's the
newest marble in **this** box?". `OuterRef` is the finger pointing at the box on
the outside.

```python
from django.db.models import OuterRef, Subquery

ultimo_comentario = (
    Comment.objects
    .filter(post=OuterRef("pk"))       # "of this post" (the outer one)
    .order_by("-created_at")
    .values("author_name")[:1]
)

Post.objects.annotate(ultimo_autor=Subquery(ultimo_comentario))
```

- **`OuterRef("pk")`** points to the object in the outer query.
- **`Subquery(...)[:1]`** brings **one** value per outer row.

### `Exists`: an efficient "is there any?"

```python
from django.db.models import Exists, OuterRef

tem_comentario = Comment.objects.filter(post=OuterRef("pk"))
Post.objects.annotate(comentado=Exists(tem_comentario)).filter(comentado=True)
```

!!! tip "`Exists` is faster than `Count > 0`"
    To know only *whether something exists*, `Exists` stops at the first row;
    `Count` scans everything. Use `Exists` when you only want yes/no.

### Database functions: math and text in the database

```python
from django.db.models import Value
from django.db.models.functions import Coalesce, Concat, Lower, Length, TruncMonth

# join first + last name in the database
Author.objects.annotate(full=Concat("first_name", Value(" "), "last_name"))

# use a fallback when the value is null
Post.objects.annotate(quando=Coalesce("published_at", "created_at"))

# group by month
Post.objects.annotate(mes=TruncMonth("published_at")).values("mes").annotate(n=Count("id"))
```

| Function | What it does |
| --- | --- |
| `Coalesce(a, b)` | First non-null value |
| `Concat(...)` | Joins text |
| `Lower` / `Upper` | Text case |
| `Length` | Text length |
| `Trunc*` (`TruncDate`/`TruncMonth`...) | Truncates the date to group by |
| `Cast` | Converts type |
| `Now` | Database date/time |

### `F`: arithmetic and comparison between columns

```python
from django.db.models import F

# increment without a race condition (in the database)
Post.objects.filter(pk=1).update(views=F("views") + 1)

# compare two columns of the same record
Post.objects.filter(likes__gt=F("dislikes"))
```

### Window functions: ranking without losing the rows

Think like a child: numbering the marbles of each box **without** piling them
into a heap — each marble stays right where it is, it just gets a number.

```python
from django.db.models import F, Window
from django.db.models.functions import RowNumber, Rank

Post.objects.annotate(
    posicao=Window(
        expression=RowNumber(),
        partition_by=[F("author")],        # restart the count per author
        order_by=F("published_at").desc(),
    )
)
```

| Window function | Gives |
| --- | --- |
| `RowNumber` | Sequential number (1,2,3...) |
| `Rank` / `DenseRank` | Ranking (with/without gaps on ties) |
| `Lag` / `Lead` | Value of the previous/next row |

!!! danger "Expressions run in the DATABASE, not in Python"
    The whole point is for the database to do the math and hand it back ready — a
    single query, no N+1, no loop in Python. If you catch yourself pulling objects
    and summing/counting them in a `for`, you can almost always push that down into
    an expression.

!!! quote "📖 In the official docs"
    - [Query expressions](https://docs.djangoproject.com/en/stable/ref/models/expressions/)
    - [Database functions](https://docs.djangoproject.com/en/stable/ref/models/database-functions/)

## Recap

- Expressions ask the **database** to do the math: one query, result ready.
- `Case`/`When` = if/else; `Count(filter=Q(...))` = conditional aggregation.
- `Subquery`+`OuterRef` = correlated query per row; `Exists` = efficient yes/no.
- Database functions (`Coalesce`, `Concat`, `Trunc*`, `Cast`) transform data in
  the database; `F` does arithmetic/comparison between columns.
- Window functions rank/number without collapsing the rows.
- Rule: counted/summed in a Python `for`? An expression probably fits.

Math mastered. Make sure nothing breaks as things evolve: **[testing in depth](testing.md)**.
