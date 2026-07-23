# Django sync × async

Django was born **synchronous**: one request occupies a worker from start to finish.
Since version 3+ it also speaks **async** — `async def` views, an asynchronous ORM,
ASGI. This page explains **when** async helps (and when it doesn't) before the
[hands-on example](async-example.md).

!!! quote "Think like a child 🧒"
    Picture a waiter (the worker). In **synchronous** mode, he takes your order to
    the kitchen and **stands there** waiting for the dish to be ready, serving
    nobody else. In **asynchronous** mode, he jots down your order, goes to serve
    other tables, and comes back when the dish is ready. Same waiter, many more
    tables served — **as long as** there's some waiting (I/O) to take advantage of.

## What changes: WSGI × ASGI

| | Synchronous (WSGI) | Asynchronous (ASGI) |
| --- | --- | --- |
| Server | Gunicorn | Uvicorn / Daphne |
| View | `def` | `async def` |
| Concurrency | 1 request per worker/thread | many per worker (at each `await`) |
| Real gain | — | When the view **waits on I/O** |

!!! info "Async isn't 'faster' — it's 'more concurrent'"
    An async view does **not** crunch CPU any faster. The gain shows up when it
    **waits** on something (the database, an external API, a file): while it waits,
    the worker serves another request. If the view only does computation (CPU),
    async won't help — it may even get in the way.

## When to use async

!!! tip "Async shines when..."
    - The view makes **many I/O calls** that can run in parallel (e.g. calling
      3 external APIs at the same time).
    - You keep **long-lived connections** (SSE, WebSocket via [Channels](../libs/channels.md)).
    - There's **a lot of waiting** per request and you want to hold more simultaneous
      connections on the same hardware.

!!! warning "Stay synchronous when..."
    - The app is a plain CRUD (most of them!) — synchronous is simpler and just as
      fast.
    - The work is **CPU-bound** (image processing, heavy computation) → that belongs
      in a [Celery task](../libs/celery.md), not in async.
    - Your stack (drivers, libs) is still sync — mixing it badly is a headache.

## The asynchronous ORM

Every database operation gained a version with an **`a`** prefix, and iteration uses
**`async for`**:

| Synchronous | Asynchronous |
| --- | --- |
| `for p in qs:` | `async for p in qs:` |
| `Model.objects.get(...)` | `await Model.objects.aget(...)` |
| `.first()` / `.count()` / `.exists()` | `await .afirst()` / `.acount()` / `.aexists()` |
| `Model.objects.create(...)` | `await Model.objects.acreate(...)` |
| `obj.save()` / `obj.delete()` | `await obj.asave()` / `await obj.adelete()` |
| `get_object_or_404(...)` | `await aget_object_or_404(...)` |

```python
# materialize the queryset into a list before the template
posts = [post async for post in Post.objects.published()]

# a single object
post = await aget_object_or_404(Post.objects.published(), slug=slug)

# writing
await Comment.objects.acreate(post=post, author_name="Ana", body="hi")
```

!!! danger "The #1 mistake: `SynchronousOnlyOperation`"
    Calling the **synchronous** ORM inside an async view raises
    `SynchronousOnlyOperation`. For example, `post.author` fires a synchronous query if
    the author wasn't preloaded. Fixes:

    - Use the **async API** (`aget`, `async for`, `acreate`).
    - **Preload** relations with `select_related`/`prefetch_related` and
      materialize the list **before** rendering the template.
    - For unavoidable sync code that touches the database, wrap it in
      `sync_to_async(...)`.

## Mixing the two worlds

Think like a child: `sync_to_async` is the **translator** that lets the async waiter
talk to the synchronous kitchen, and `async_to_sync` does the reverse.

```python
from asgiref.sync import sync_to_async, async_to_sync

# call SYNCHRONOUS code from inside an async view
resultado = await sync_to_async(funcao_sync_que_usa_orm)()

# call ASYNC code from inside synchronous code (e.g. a command)
async_to_sync(minha_corotina)()
```

!!! info "Views, middleware and ORM are async; plenty is still sync"
    Django lets you mix: an async view can call sync helpers (via
    `sync_to_async`), and the framework adapts sync/async middleware automatically.
    Management commands, signals and most third-party libs are still
    synchronous — and that's fine.

## How to serve

```bash
# synchronous
gunicorn config.wsgi:application

# asynchronous (required for async views to deliver real concurrency)
uvicorn config.asgi:application
```

!!! warning "An async view under WSGI gains nothing"
    If you serve async views with Gunicorn/WSGI, Django runs them in a compatibility
    layer and the concurrency gain **vanishes**. Async needs an **ASGI** server
    (Uvicorn/Daphne). See [deploy](../referencia/deploy.md).

## Recap

- Async = more **concurrency** under I/O, not more CPU speed. Most apps (CRUD) live
  happily on synchronous.
- WSGI (`def`, Gunicorn) × ASGI (`async def`, Uvicorn); async needs an ASGI server
  to be worth it.
- Async ORM: the `a` prefix (`aget`/`acreate`/`asave`) and `async for`; materialize
  lists and preload relations before the template.
- Watch out for `SynchronousOnlyOperation`; use `sync_to_async`/`async_to_sync`
  to cross the worlds.
- CPU-bound → Celery, not async.

!!! quote "📖 In the official docs"
    - [Async support (Django)](https://docs.djangoproject.com/en/stable/topics/async/)
    - [Asynchronous ORM queries](https://docs.djangoproject.com/en/stable/topics/db/queries/#asynchronous-queries)

Now see the whole blog **rewritten in async**: the
**[asynchronous example](async-example.md)**.
