# Reference: cache

!!! quote "Think like a child 🧒"
    Every time someone asks "what's 7×8?", you can recompute it... or remember you
    just answered 56 a moment ago and say it instantly. The **cache** is that
    memory of ready-made answers: you stash the expensive result in a quick little
    drawer and, next time, grab it from there instead of redoing the math (or the
    query).

## Use case

A "most popular posts" page runs a heavy query. It barely changes — there's no
point recomputing it on every visit. You stash the result for 5 minutes:

```python
from django.core.cache import cache

def get_popular_posts() -> list[Post]:
    """Return popular posts, cached for 5 minutes."""
    posts = cache.get("popular_posts")            # (1)!
    if posts is None:                              # (2)!
        posts = list(Post.objects.popular()[:10])
        cache.set("popular_posts", posts, timeout=300)
    return posts
```

1. Tries to grab it from the little drawer.
2. If it wasn't there (or expired), compute it and stash it. This pattern is
    *cache-aside* — the most common one.

## Possibilities

### Configuring the backend: `CACHES`

| Backend | Where it stores | Good for |
| --- | --- | --- |
| `LocMemCache` (default) | Process memory | Dev, tests |
| `RedisCache` | Redis | Production (shared across processes) |
| `DatabaseCache` | A table in the database | When Redis isn't available |
| `FileBasedCache` | Files on disk | Simple cases |
| `DummyCache` | Stores nothing | Turning cache off in dev |

```python
# production with Redis
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379",
    }
}
```

!!! warning "`LocMemCache` is not shared"
    It lives in the memory of **one** process. With multiple workers (Gunicorn),
    each one has its own cache — which gets confusing. In production with multiple
    processes, use Redis.

### The low-level API (the most useful one)

Think like a child: the little drawer has only four moves — put, grab, take out,
"grab or compute".

| Method | What it does |
| --- | --- |
| `cache.set(key, value, timeout)` | Stores it (timeout in seconds; `None` = forever) |
| `cache.get(key, default)` | Grabs it (or the default) |
| `cache.add(key, value)` | Stores it only if it doesn't exist yet |
| `cache.get_or_set(key, callable, timeout)` | Grabs it; if missing, calls and stores |
| `cache.delete(key)` | Takes it out |
| `cache.incr/decr(key)` | Adds/subtracts (counters) |
| `cache.set_many / get_many` | In batches |
| `cache.clear()` | Empties everything |

```python
# get_or_set: cache-aside in one line
posts = cache.get_or_set(
    "popular_posts",
    lambda: list(Post.objects.popular()[:10]),
    timeout=300,
)
```

### Caching an entire view

```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)      # 15 minutes
def home(request): ...
```

In a CBV, decorate `dispatch` with `method_decorator`:

```python
from django.utils.decorators import method_decorator

@method_decorator(cache_page(60 * 15), name="dispatch")
class HomeView(TemplateView): ...
```

### Caching a piece of a template

```django
{% load cache %}
{% cache 300 sidebar request.user.id %}
  ... expensive sidebar content ...
{% endcache %}
```

`request.user.id` is a **vary key**: each user gets their own version.

### `cached_property`: cache inside an object

Think like a child: compute once per object and keep it on the object itself.

```python
from django.utils.functional import cached_property

class Post(models.Model):
    @cached_property
    def comment_count(self) -> int:
        """Count comments once per instance."""
        return self.comments.count()
```

Accessing `post.comment_count` several times runs the query **once** only.

!!! danger "Invalidating cache is the hard problem"
    Storing is easy; knowing **when to throw it away** is what hurts. Strategies:

    - **Short timeout** (simplest): accept slightly stale data.
    - **Invalidation by key**: on `post_save`, `cache.delete("popular_posts")`.
    - **Versioned key**: include something that changes (e.g. `updated_at`) in the key.

    Start with a timeout. Only complicate things when "stale data for N minutes"
    isn't acceptable.

## Recap

- Cache stashes expensive results in a quick little drawer (the *cache-aside*
  pattern: `get` → if `None`, compute and `set`).
- `CACHES` chooses the backend; use **Redis** in production (shared),
  `LocMemCache` only in dev.
- Low level: `set`/`get`/`add`/`get_or_set`/`delete`/`incr`. `get_or_set` is the
  shortcut.
- Whole view: `cache_page` (+`method_decorator` in a CBV); a template piece:
  `{% cache %}`; per object: `cached_property`.
- The hard part is **invalidation**: start with a short timeout, evolve toward
  invalidation by key on `post_save`.

Cache speeds things up. For tasks outside the web cycle, you write your own
commands: **[management commands](management-commands.md)**.
