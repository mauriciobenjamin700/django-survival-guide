# django-filter

Listings almost always need filters: "posts with the django tag", "orders between
two dates", "products over $50". Writing that by hand in every view gets tiring. **django-filter** turns URL **query params** (`?tag=django&preco__gt=50`)
into queryset filters — in Django and in DRF.

!!! quote "Think like a child 🧒"
    Imagine a giant toy box and a **sieve** with holes you get to
    choose: "only the red ones", "only the big ones". django-filter is that configurable
    sieve: the user picks the holes through the URL, and only what passes shows up.

## Installation

```bash
uv add django-filter
```

```python
# settings.py
INSTALLED_APPS = ["django_filters", ...]
```

## What you can do

### A FilterSet: declare the sieve's holes

```python
# apps/blog/filters.py
import django_filters

from apps.blog.models import Post


class PostFilter(django_filters.FilterSet):
    """Declarative filters for the Post list."""

    title = django_filters.CharFilter(lookup_expr="icontains")   # (1)!
    tag = django_filters.CharFilter(field_name="tags__slug")     # (2)!
    published_after = django_filters.DateFilter(
        field_name="published_at", lookup_expr="gte",
    )

    class Meta:
        model = Post
        fields = ["status"]        # (3)!
```

1. `?title=orm` matches any title containing "orm" (case-insensitive).
2. `?tag=django` traverses the relation down to `tags.slug`.
3. Automatic "exact" filters: `?status=published`. You list the field, and
    django-filter creates the filter.

### In DRF (the most common use)

```python
# settings.py
REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
}
```

```python
# apps/blog/api/views.py
from django_filters.rest_framework import DjangoFilterBackend


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PostFilter        # (1)!
```

1. Or the shortcut `filterset_fields = ["status", "author"]` for exact filters without
    writing a FilterSet.

Now the API accepts: `GET /api/posts/?status=published&tag=django&published_after=2026-01-01`.

### In class-based views (HTML)

```python
from django_filters.views import FilterView


class PostListView(FilterView):
    model = Post
    filterset_class = PostFilter
    template_name = "blog/post_list.html"
```

```django
<form method="get">
  {{ filter.form.as_p }}      {# generates the filter fields #}
  <button type="submit">Filter</button>
</form>
{% for post in filter.qs %}{{ post.title }}{% endfor %}
```

!!! tip "Filtering uses GET, not POST"
    A filter is a **search** — the criteria go in the URL (`?tag=...`), so you can
    share the link and paginate while keeping the filter. That's why the `<form
    method="get">`. It pairs with [pagination](../tutorial/pagination.md).

### Common filter types

| Filter | For |
| --- | --- |
| `CharFilter` | Text (with `lookup_expr="icontains"` for "contains") |
| `NumberFilter` | Numbers (`lookup_expr="gte"/"lte"`) |
| `DateFilter` / `DateFromToRangeFilter` | Date / date range |
| `BooleanFilter` | Yes/no |
| `ChoiceFilter` | A fixed list of options |
| `ModelChoiceFilter` | Choosing a related object |
| `OrderingFilter` | Letting the client sort (`?ordering=-published_at`) |

!!! warning "Restrict what can be filtered/ordered"
    Don't accidentally expose internal fields. List the filters explicitly; for
    ordering, use `OrderingFilter(fields=[...])` with a closed list — otherwise the
    client sorts by any column, which can leak information or strain the
    database.

## Recap

- django-filter turns **query params** (`?field=value`) into queryset filters,
  declared in a `FilterSet`.
- Each filter defines `field_name` (the field, traverses with `__`) and `lookup_expr`
  (`icontains`, `gte`...).
- In DRF: `DjangoFilterBackend` + `filterset_class` (or `filterset_fields`).
- In HTML: `FilterView` + `{{ filter.form }}`; filtering uses **GET** and pairs with
  pagination.
- Restrict filterable/orderable fields explicitly.

!!! quote "📖 In the official docs"
    - [django-filter](https://django-filter.readthedocs.io/)

One thing left to know: the tools every project ends up using —
**[the friends catalog](afins.md)**.
