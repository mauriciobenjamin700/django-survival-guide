# Asynchronous example (async blog)

The repository ships a **second project**, `example_async/`, with the same blog
rewritten in **Django async**. Here we unpack what changes compared to the
[synchronous example](../tutorial/project-setup.md). Read
[sync × async](sync-vs-async.md) first for the why.

!!! quote "Think like a child 🧒"
    It's the same blog — the same boxes (models), the same screens. We only swapped
    the synchronous waiter for the asynchronous one: the views become `async def` and
    talk to the database through the `a...` API. Nothing else has to change.

## Running it

```bash
cd example_async
uv run python manage.py migrate
uv run python manage.py seed_blog
uv run uvicorn config.asgi:application --reload      # (1)!
```

1. **Uvicorn** (ASGI), not `runserver`/Gunicorn — that's what makes the async views
    deliver real concurrency.

## What's identical

- **Models** (`Post`, `Author`, `Tag`, `Comment`) — the schema doesn't change between
  sync and async.
- **Templates** — rendering is the same; we just hand over ready-made lists.
- **URLs** — async functions go into `path()` just like the synchronous ones.

## What changes: the views

Comparing the same `post_detail` in both styles:

=== "Sync"

    ```python
    from django.shortcuts import get_object_or_404, render

    def post_detail(request, slug):
        post = get_object_or_404(Post.objects.published().select_related("author"), slug=slug)
        comments = post.approved_comments()
        return render(request, "blog/post_detail.html",
                      {"post": post, "comments": comments, "form": CommentForm()})
    ```

=== "Async"

    ```python
    from django.shortcuts import aget_object_or_404, render

    async def post_detail(request, slug):
        post = await aget_object_or_404(
            Post.objects.published().select_related("author"), slug=slug,
        )
        comments = [c async for c in post.approved_comments()]   # (1)!
        return render(request, "blog/post_detail.html",
                      {"post": post, "comments": comments, "form": CommentForm()})
    ```

1. `async for` + materialize into a list: the template iterates synchronously, so we
    resolve the database **beforehand**.

### The list

```python
async def post_list(request):
    posts = [
        post
        async for post in Post.objects.published().select_related("author")
    ]
    return render(request, "blog/post_list.html", {"posts": posts})
```

### Writing on POST

```python
async def comment_create(request, slug):
    post = await aget_object_or_404(Post.objects.published(), slug=slug)
    form = CommentForm(request.POST)          # (1)!
    if form.is_valid():
        await Comment.objects.acreate(post=post, **form.cleaned_data)   # (2)!
    return HttpResponseRedirect(post.get_absolute_url())
```

1. Form validation is synchronous (pure CPU) — you can call `is_valid()` directly.
2. The write uses `acreate` (async). If we used `form.save()` (synchronous, touches
    the database) it would raise `SynchronousOnlyOperation` — hence `acreate` with
    `cleaned_data`.

!!! danger "Materialize before the template; preload relations"
    Two precautions that prevent `SynchronousOnlyOperation`:

    - Turn the queryset into a **list** with `async for` before passing it to the
      template (the template can't do `await`).
    - Use `select_related`/`prefetch_related` so the template doesn't fire a
      synchronous query when accessing `post.author`.

## Synchronous `render` in an async view?

Yes — in this version of Django there's no `arender`, and `render` does **not** touch
the database (the data already came materialized), so calling it directly is safe. If
you ever need truly asynchronous rendering, use `sync_to_async(render)(...)`.

## What did NOT become async

- **Management commands** (`seed_blog`) — they run sync; they use the normal ORM.
- **Admin** — Django's admin is synchronous.
- **Forms** — validation is CPU; only persistence moved to `acreate`.

This is normal: async is about **serving requests** with concurrency, not about
making everything asynchronous.

## When this blog benefits from async

Honestly? A CRUD blog does **not** gain much from async — it's the teaching example.
The gain would appear if the view, say, called **several external APIs** in parallel
(`asyncio.gather`) or held long-lived connections
([SSE](../libs/sse.md)/[WebSocket](../libs/channels.md)). The value here is
**learning the pattern** with something familiar.

## Recap

- `example_async/` is the same blog in Django async: identical models/templates/URLs,
  **`async def` views** with the `a...` ORM (`aget_object_or_404`, `async for`,
  `acreate`).
- Materialize lists and preload relations before the template; sync `render` is
  fine because it doesn't touch the database.
- Serve it with **Uvicorn (ASGI)**; commands/admin/forms stay synchronous.
- For a CRUD, async is didactic; the real gain is with concurrent I/O and long-lived
  connections.

!!! quote "📖 In the official docs"
    - [Async views (Django)](https://docs.djangoproject.com/en/stable/topics/async/)
    - [ASGI deployment (Django)](https://docs.djangoproject.com/en/stable/howto/deployment/asgi/)

Concept and practice covered. Head back to [sync × async](sync-vs-async.md) or to the
[reference map](../referencia/index.md).
