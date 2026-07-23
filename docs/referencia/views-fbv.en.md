# Reference: function-based views (FBV)

This guide prefers [class-based views](views-cbv.md), but Django supports both
styles — and many people **prefer functions**: they are explicit, linear and easy
to read top to bottom. This page shows the same blog in FBV style.

!!! quote "Think like a child 🧒"
    A class-based view is an appliance with ready-made buttons you tune. A
    **function** view is a handwritten recipe: you read it line by line, start to
    finish, and see **exactly** what happens. Nothing hidden — what's written is
    what runs.

## Use case

A view function receives the `request` and returns a response. You decide
everything:

```python
# apps/blog/views.py
from django.shortcuts import get_object_or_404, render
from django.http import HttpRequest, HttpResponse

from apps.blog.models import Post


def post_list(request: HttpRequest) -> HttpResponse:
    """Show the list of published posts."""
    posts = Post.objects.published().select_related("author")
    return render(request, "blog/post_list.html", {"posts": posts})


def post_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """Show a single published post."""
    post = get_object_or_404(Post.objects.published(), slug=slug)
    return render(request, "blog/post_detail.html", {"post": post})
```

```python
# apps/blog/urls.py — no .as_view(): the function goes in directly
urlpatterns = [
    path("", views.post_list, name="post-list"),
    path("posts/<slug:slug>/", views.post_detail, name="post-detail"),
]
```

!!! info "In urls.py, FBV is more direct"
    A CBV needs `PostListView.as_view()`; an FBV goes in **directly**
    (`views.post_list`), because it already is the function the router expects.

## Possibilities

### The day-to-day tools

| Tool | Does |
| --- | --- |
| `render(request, template, context)` | Renders a template into a response |
| `redirect("name" or obj)` | Redirects (301/302) |
| `get_object_or_404(qs, **kw)` | Fetch one object or raise 404 |
| `get_list_or_404(qs, **kw)` | List or 404 if empty |
| `HttpResponse` / `JsonResponse` | Raw / JSON response |
| `request.method` / `request.POST` / `request.GET` | Request data |

### Handling GET and POST in the same view

In an FBV you branch on the method **explicitly** — what the CBV does with
separate methods:

```python
from django.shortcuts import redirect

from apps.blog.forms import PostForm


def post_create(request: HttpRequest) -> HttpResponse:
    """Create a post: show the form on GET, save it on POST."""
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user.author_profile
            post.save()
            form.save_m2m()                      # (1)!
            return redirect(post.get_absolute_url())
    else:
        form = PostForm()
    return render(request, "blog/post_form.html", {"form": form})
```

1. `commit=False` defers saving so you can set the author; `save_m2m()` then writes
    the M2M relations (tags) — the CBV handles this behind the scenes.

!!! tip "The classic FBV pattern"
    `if request.method == "POST":` validates and acts; the `else` shows the empty
    form. A single `render` at the end serves both GET and an invalid POST (with
    errors). It's verbose, but you **see** the whole flow.

### Decorators: the equivalent of mixins

What mixins do for CBVs, **decorators** do for FBVs:

```python
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods


@login_required
@require_http_methods(["GET", "POST"])       # (1)!
def post_create(request: HttpRequest) -> HttpResponse:
    ...


@permission_required("blog.delete_post")
def post_delete(request: HttpRequest, slug: str) -> HttpResponse:
    ...
```

1. Restricts the accepted methods — a POST to a GET-only route becomes a 405.

| Decorator | Equivalent mixin |
| --- | --- |
| `@login_required` | `LoginRequiredMixin` |
| `@permission_required("app.perm")` | `PermissionRequiredMixin` |
| `@user_passes_test(fn)` | `UserPassesTestMixin` |
| `@require_http_methods([...])` / `@require_POST` | `http_method_names` |
| `@cache_page(60)` | (view caching) |

!!! warning "Decorator order matters"
    Decorators apply bottom-up (the one closest to the function first). Put
    `@login_required` on top so it gates before anything else runs.

### FBV in DRF: `@api_view`

DRF also has a function style:

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from apps.blog.api.serializers import PostSerializer


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticatedOrReadOnly])
def posts(request):
    """List posts (GET) or create one (POST)."""
    if request.method == "POST":
        serializer = PostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user.author_profile)
        return Response(serializer.data, status=201)
    qs = Post.objects.published()
    return Response(PostSerializer(qs, many=True).data)
```

## FBV × CBV: when to use each

| | FBV (function) | CBV (class) |
| --- | --- | --- |
| Readability | Linear, all in sight | Spread across methods/inheritance |
| Reuse | Copy/paste or helpers | Inheritance and mixins |
| Repetitive CRUD | Verbose | Concise (generic views) |
| Unique/atypical logic | Great | Can "fight" the ready-made flow |
| Learning curve | Lower | Higher (MRO, hooks) |

!!! tip "It's not religion — mix them"
    Use **CBVs** for repetitive CRUD (list/detail/create/update/delete), where
    generic views save a lot. Use **FBVs** for one-off views, atypical flows, or
    when linear clarity beats reuse. A healthy project has both. Choose by
    readability, not dogma.

## Recap

- An FBV takes `request` and returns a response; in `urls.py` it goes in directly
  (no `.as_view()`).
- Tools: `render`, `redirect`, `get_object_or_404`, `request.method/POST/GET`.
- Handle GET/POST with `if request.method == "POST":`; `commit=False` + `save_m2m()`
  on create.
- **Decorators** replace mixins (`@login_required`, `@require_POST`,
  `@permission_required`); order matters.
- DRF has `@api_view`. Choose FBV×CBV by **readability and reuse**, and mix them.

!!! quote "📖 In the official docs"
    - [Writing views (Django)](https://docs.djangoproject.com/en/stable/topics/http/views/)
    - [View decorators (Django)](https://docs.djangoproject.com/en/stable/topics/http/decorators/)

For the object-oriented style, see [class-based views](views-cbv.md).
