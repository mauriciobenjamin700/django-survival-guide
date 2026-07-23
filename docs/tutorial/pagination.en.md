# Pagination

A list of 3 posts fits on one screen. With 3,000, it doesn't. **Pagination** is
breaking a big list into pages — better for the user and for the database (you
fetch only one chunk at a time).

!!! quote "The idea"
    Think of a book: instead of one giant rolled-up sheet, the content comes in
    numbered pages. You read page 1, turn to page 2. Pagination does that with your
    post list.

## The easy way: `paginate_by` on the `ListView`

Our `PostListView` already paginates — it took just **one line**:

```python
class PostListView(ListView):
    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 5          # (1)!
```

1. Five posts per page. The `ListView` handles the rest: it reads the `?page=`
    parameter from the URL, slices the queryset, and exposes the navigation objects
    in the template.

With that, the view puts into the context:

| Variable | What it is |
| --- | --- |
| `page_obj` | The current page (with the items and the navigation) |
| `paginator` | The paginator (total pages/items) |
| `is_paginated` | `True` if there's more than one page |
| `posts` | The items on **this** page (via `context_object_name`) |

## Navigating in the template

```django
{% for post in posts %}
  <h2>{{ post.title }}</h2>
{% endfor %}

{% if is_paginated %}
  <nav>
    {% if page_obj.has_previous %}
      <a href="?page={{ page_obj.previous_page_number }}">← Previous</a>
    {% endif %}

    <span>Page {{ page_obj.number }} of {{ page_obj.paginator.num_pages }}</span>

    {% if page_obj.has_next %}
      <a href="?page={{ page_obj.next_page_number }}">Next →</a>
    {% endif %}
  </nav>
{% endif %}
```

| `page_obj` attribute | Gives |
| --- | --- |
| `.number` | Current page number |
| `.has_next` / `.has_previous` | Is there a next/previous? |
| `.next_page_number` / `.previous_page_number` | Neighboring numbers |
| `.paginator.num_pages` | Total pages |
| `.paginator.count` | Total items |
| `.start_index` / `.end_index` | Range of items shown (e.g. "6–10 of 42") |

!!! warning "Preserve the other URL parameters"
    If the list also filters by tag (`?tag=django`), the page links need to
    **keep** the filter, otherwise page 2 loses it:
    ```django
    <a href="?page={{ page_obj.next_page_number }}{% if active_tag %}&tag={{ active_tag }}{% endif %}">
    ```

## How it works underneath: `Paginator`

Think like a child: the `Paginator` is the one who cuts the cake into equal
slices. The `ListView` uses it for you, but you can use it directly:

```python
from django.core.paginator import Paginator

posts = Post.objects.published()
paginator = Paginator(posts, 5)         # 5 per page

page = paginator.get_page(2)            # page 2 (robust)
page.object_list                        # the 5 items
page.has_next()                         # True/False
```

!!! tip "`get_page` vs `page`"
    - **`get_page(n)`** is fool-proof: an invalid or out-of-range number falls back
      to a valid page (1 or the last one). Always prefer it.
    - **`page(n)`** raises an exception (`EmptyPage`, `PageNotAnInteger`) for bad
      values — you'd have to handle it by hand.

## Efficiency

!!! info "Pagination is already efficient"
    The queryset is lazy: `paginate_by = 5` makes Django fetch **only** the 5 items
    of the page (via `LIMIT/OFFSET`), plus a `COUNT` to know the total. It doesn't
    load the whole list into memory.

!!! danger "A large OFFSET is slow"
    On huge datasets, `?page=100000` uses a giant `OFFSET` and gets slow (the
    database skips many rows). For extreme scale, there's *keyset pagination*
    (paginate by a cursor, e.g. `created_at < X`). For a blog, the default
    `Paginator` is perfect.

!!! quote "📖 In the official docs"
    - [Pagination](https://docs.djangoproject.com/en/stable/topics/pagination/)

## Recap

- `paginate_by = N` on the `ListView` turns on pagination for free.
- In the template: `page_obj` (`.number`, `.has_next`...), `paginator.num_pages`,
  `is_paginated`. **Preserve** the filters in the page links.
- Underneath it's the `Paginator`; use `get_page(n)` (robust), not `page(n)`.
- It's efficient by default (`LIMIT/OFFSET` + `COUNT`); only a giant `OFFSET`
  hurts.

After acting (creating, commenting), it's good to tell the user. In come the
**[messages](messages.md)**.
