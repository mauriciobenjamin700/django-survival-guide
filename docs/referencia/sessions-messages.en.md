# Reference: sessions and messages

!!! quote "Think like a child 🧒"
    The site forgets you at every click — each request is a brand new person
    arriving. The **session** is a little backpack kept on the server with a tag;
    you carry only the tag (a cookie) and, on each visit, the server grabs your
    backpack back. **Messages** are little notes: you stick one on ("saved
    successfully!"), it shows up **once** on the next screen and then disappears.

## Use case

### Session: remembering something between pages

```python
def add_to_cart(request: HttpRequest, product_id: int) -> HttpResponse:
    """Store the cart in the session so it survives across requests."""
    cart: list[int] = request.session.get("cart", [])
    cart.append(product_id)
    request.session["cart"] = cart          # (1)!
    return redirect("cart")
```

1. Writing to a key marks the session as "dirty" and Django saves it on its own.

### Message: notifying the user on the next screen

```python
from django.contrib import messages

def form_valid(self, form):
    response = super().form_valid(form)
    messages.success(self.request, "Post published successfully!")
    return response
```

```django
{% for message in messages %}
  <p class="alert {{ message.tags }}">{{ message }}</p>
{% endfor %}
```

## Possibilities

### Sessions: the API

| Operation | Code |
| --- | --- |
| Read (with default) | `request.session.get("key", default)` |
| Write | `request.session["key"] = value` |
| Delete a key | `del request.session["key"]` |
| Exists? | `"key" in request.session` |
| Expiry | `request.session.set_expiry(3600)` (seconds; `0` = when the browser closes) |
| Empty everything | `request.session.flush()` (use it on logout) |

!!! tip "Django detects most changes on its own"
    Assigning (`session["x"] = ...`) marks it dirty and saves. But **deep
    mutation** (e.g. `session["cart"].append(x)` without reassigning) can slip
    through unnoticed — that's why the cart example reassigns `session["cart"] =
    cart`. When in doubt, `request.session.modified = True`.

### Where the backpack is kept: `SESSION_ENGINE`

| Backend | Where it stores | Good for |
| --- | --- | --- |
| `db` (default) | A table in the database | General use |
| `cache` | In the cache (e.g. Redis) | Speed |
| `cached_db` | Cache + database | Speed + durability |
| `signed_cookies` | In the cookie itself (signed) | Stateless on the server (mind the size) |

```python
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_COOKIE_AGE = 1209600   # 2 weeks, in seconds
```

!!! danger "The cookie carries only the tag, not the backpack"
    With the server-side backends, the cookie holds only the session **id**. The
    data lives on the server. With `signed_cookies`, the data travels in the
    cookie (signed, not encrypted) — never put secrets there, and watch out for
    the ~4KB limit.

### Messages: levels and usage

Think like a child: each little note has a color to match its tone.

| Function | Level | Typical use |
| --- | --- | --- |
| `messages.debug(request, ...)` | DEBUG | Development only |
| `messages.info(request, ...)` | INFO | Neutral information |
| `messages.success(request, ...)` | SUCCESS | "It worked!" |
| `messages.warning(request, ...)` | WARNING | Heads up |
| `messages.error(request, ...)` | ERROR | Something failed |

`{{ message.tags }}` in the template becomes the CSS class (`success`, `error`...)
for you to style.

!!! info "A message shows up ONCE and disappears"
    Messages use the *flash* pattern: they're stored (in the session) until they're
    **displayed**, and then discarded. Perfect for "saved successfully" after a
    redirect — it won't repeat on the next navigation.

### `SuccessMessageMixin`: the shortcut for CBVs

```python
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import CreateView


class PostCreateView(SuccessMessageMixin, CreateView):
    model = Post
    fields = ["title", "body"]
    success_message = "Post “%(title)s” created!"    # (1)!
```

1. `%(title)s` is filled in with the `title` field of the saved object.

## Recap

- The **session** is the backpack on the server; the cookie carries only the tag
  (id). A dict-like API: `get`/`[]=`/`del`/`flush`; `set_expiry` controls validity.
- Reassign when mutating nested structures (or `session.modified = True`).
- `SESSION_ENGINE` chooses where to store (db/cache/cached_db/signed_cookies).
- **Messages** are flash notes: `success`/`info`/`warning`/`error`, displayed once
  and discarded; `{{ message.tags }}` gives the CSS class.
- In CBVs, `SuccessMessageMixin` + `success_message` is the shortcut.

Storing state quickly leads to the next topic: **[cache](cache.md)**.
