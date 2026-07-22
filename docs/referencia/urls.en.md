# Reference: URLs and converters

!!! quote "Think like a child 🧒"
    The URL is the **address of the house**. The `urls.py` is the mail carrier: it
    looks at the address written on the envelope (what you type in the browser) and
    knows which door (which view) to deliver it to. A **converter** is the mail
    carrier checking the format: "this part has to be a number", "this one has to
    be a name with hyphens".

## Use case

You want `/posts/ola-mundo/` to show the post with slug `ola-mundo`, and
`/posts/42/` to not be accepted as a slug. You map the route, capture the variable
part with a converter, and it arrives at the view:

```python
# apps/blog/urls.py
from django.urls import URLPattern, path

from apps.blog import views

app_name = "blog"

urlpatterns: list[URLPattern] = [
    path("", views.PostListView.as_view(), name="post-list"),
    path("posts/<slug:slug>/", views.PostDetailView.as_view(), name="post-detail"),
]
```

The `<slug:slug>` captures `ola-mundo` and hands it to the view in
`self.kwargs["slug"]`. Let's look at all the pieces.

## Possibilities

### `path()` vs `re_path()`

| Function | How it matches the route |
| --- | --- |
| `path()` | Simple syntax with `<type:name>` converters (use it almost always) |
| `re_path()` | Regular expression (for patterns `path` can't express) |

```python
from django.urls import path, re_path

path("posts/<int:year>/<slug:slug>/", view)             # simple
re_path(r"^posts/(?P<year>[0-9]{4})/$", view)           # regex
```

### Built-in converters

| Converter | Matches | Example value |
| --- | --- | --- |
| `str` | Text without `/` (the default if you omit the type) | `ola-mundo` |
| `int` | Integers ≥ 0 | `42` |
| `slug` | Letters, numbers, hyphen and underscore | `meu-post-1` |
| `uuid` | A formatted UUID | `075194d3-...` |
| `path` | Text **including** `/` (grabs the rest) | `docs/guia/intro` |

```python
path("artigo/<uuid:id>/", view)
path("arquivo/<path:caminho>/", view)   # caminho may contain slashes
```

!!! tip "No type = `str`"
    Is `<slug>` a shortcut for `<str:slug>`? No — `<slug>` uses the `str` converter
    with the **name** `slug`. To use the real slug converter, write the type:
    `<slug:slug>`. The first piece is the **type**, the second is the **name** of
    the argument.

### Order matters (a lot)

```python
urlpatterns = [
    path("posts/new/", views.PostCreateView.as_view(), name="post-create"),
    path("posts/<slug:slug>/", views.PostDetailView.as_view(), name="post-detail"),
]
```

!!! danger "Specific before generic"
    Django tests top to bottom and **stops at the first** one that matches. If
    `<slug:slug>` came first, `/posts/new/` would be captured as a post with slug
    `"new"`. Always put specific routes before the ones with a variable. Think like
    a child: look for the exact key before the master key.

### `include()`: split by app

The root `urls.py` delegates whole prefixes to each app:

```python
# config/urls.py
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.blog.api.urls", namespace="blog-api")),
    path("", include("apps.blog.urls", namespace="blog")),
]
```

Think like a child: the head mail carrier sees the **neighborhood** (`api/`) and
hands the envelope to the carrier for that neighborhood, who takes care of the
streets over there.

### Namespaces: names without collision

Two apps can both have a `post-list` route. The namespace disambiguates:

```python
# in the app's urls.py
app_name = "blog"                    # defines the namespace

# when referencing, use namespace:name
reverse("blog:post-detail", kwargs={"slug": "ola-mundo"})
```

### Reverse: never hand-write a URL

Think like a child: instead of memorizing the house number, you call the person by
**name** and someone takes you there. If the house moves to another street, the
name still works.

=== "In Python"

    ```python
    from django.urls import reverse, reverse_lazy

    reverse("blog:post-detail", kwargs={"slug": "ola-mundo"})   # "/posts/ola-mundo/"
    reverse_lazy("blog:post-list")   # in class attributes (deferred evaluation)
    ```

=== "In the template"

    ```django
    <a href="{% url 'blog:post-detail' post.slug %}">{{ post.title }}</a>
    ```

=== "In the model"

    ```python
    def get_absolute_url(self) -> str:
        return reverse("blog:post-detail", kwargs={"slug": self.slug})
    ```

| Function | Use it when |
| --- | --- |
| `reverse()` | Inside methods/functions (evaluated right away) |
| `reverse_lazy()` | In class attributes / settings (deferred evaluation) |
| `{% url %}` | In templates |

!!! warning "`reverse_lazy` in a class attribute"
    Class attributes (`success_url = ...`) are evaluated when the module is
    **imported** — too early, the URLs may not be loaded yet. Use `reverse_lazy`
    there; plain `reverse` inside methods.

### Passing extra arguments

```python
path("posts/<slug:slug>/", views.PostDetailView.as_view(),
     kwargs={"template": "amp"}, name="post-detail-amp")
```

## Recap

- `path()` (simple, almost always) × `re_path()` (regex).
- Converters: `str` (default), `int`, `slug`, `uuid`, `path` (accepts `/`).
  Syntax `<type:name>`.
- Order matters: **specific before generic**; Django stops at the 1st match.
- `include()` splits by app; `app_name` creates the **namespace** (`blog:post-list`).
- Always reference by **name**: `reverse`/`reverse_lazy`/`{% url %}` — never a
  literal URL.

From the URL you reach the view, which returns HTML through the
**[templates](templates.md)**.
