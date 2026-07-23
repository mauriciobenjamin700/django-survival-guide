# Reference: template engines (DTL × Jinja2)

!!! quote "Think like a child 🧒"
    A **template engine** is the one who reads the coloring page (the HTML with
    blank spaces) and fills it in with the data. Django ships with its own
    painter — the **DTL** (Django Template Language) — but it lets you hire
    another famous painter, **Jinja2**. Both paint the same picture; what changes
    is the way they hold the brush (the syntax) and the speed.

## Use case

You want to know **which** engine is rendering your pages and how Django finds
it. Everything lives in the `TEMPLATES` setting, which is a **list** — each item
is one engine:

```python
# config/settings.py
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",  # (1)!
        "DIRS": [BASE_DIR / "templates"],                              # (2)!
        "APP_DIRS": True,                                              # (3)!
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
```

1. The **engine**: here, the DTL. Swapping this string swaps the painter.
2. Project-level template folders (outside the apps).
3. `True` = it also looks inside `<app>/templates/` of every installed app.

## Possibilities

### DTL × Jinja2: when to use each

| | DTL (default) | Jinja2 |
| --- | --- | --- |
| Ships with Django | ✅ Yes | Needs installing (`jinja2`) |
| Philosophy | Limited on purpose (little logic in the template) | More powerful (allows more Python) |
| `{% url %}`, `{% csrf_token %}` | Built in | Must be exposed manually |
| Admin, auth, DRF browsable | Use DTL | — |
| Speed | Good | Usually faster |

!!! tip "Rule of thumb: stick with the DTL"
    For 95% of projects, the **DTL** is the right choice — it's the default, it
    integrates with admin/auth/messages, and it forces you to keep logic out of
    the template (which is a good thing). Consider **Jinja2** only when you need
    richer expressions in the template, or you already come from another Python
    ecosystem that uses Jinja2.

!!! info "You can use both at the same time"
    `TEMPLATES` is a list: you can register DTL **and** Jinja2 together. Django
    tries each engine in order until one of them finds the template. In practice,
    separate them by folder/extension so you don't get confused.

### Configuring Jinja2

```python
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [BASE_DIR / "jinja2"],
        "APP_DIRS": True,
        "OPTIONS": {
            "environment": "config.jinja2.environment",   # (1)!
        },
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["..."]},
    },
]
```

1. A function that builds the Jinja2 `Environment`. It's where you **re-expose**
    what the DTL gives you for free (`static`, `url`):

```python
# config/jinja2.py
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment


def environment(**options) -> Environment:
    """Build a Jinja2 environment exposing Django's static() and url()."""
    env = Environment(**options)
    env.globals.update({"static": static, "url": reverse})
    return env
```

!!! warning "With Jinja2 you lose the DTL shortcuts"
    `{% url %}`, `{% static %}`, `{% csrf_token %}`, Django filters — none of that
    exists in Jinja2 by default. You re-expose them manually in the
    `environment` (as above). Forgetting this is the #1 headache for people who
    migrate.

### Syntax side by side

=== "DTL"

    ```django
    {% for post in posts %}
      <a href="{% url 'blog:post-detail' post.slug %}">{{ post.title|upper }}</a>
    {% empty %}
      <p>No posts.</p>
    {% endfor %}
    ```

=== "Jinja2"

    ```jinja
    {% for post in posts %}
      <a href="{{ url('blog:post-detail', slug=post.slug) }}">{{ post.title|upper }}</a>
    {% else %}
      <p>No posts.</p>
    {% endfor %}
    ```

Key differences: in Jinja2 the tags become **function calls** (`url(...)`), the
empty case is `{% else %}` (not `{% empty %}`), and you can call methods with
parentheses.

### How Django finds the template: loaders

Inside the DTL, the **loaders** define *where* and *how* to look for the files:

| Loader | What it does |
| --- | --- |
| `app_directories` | Looks in `<app>/templates/` (turned on by `APP_DIRS: True`) |
| `filesystem` | Looks in the `DIRS` folders |
| `cached` | Wraps the others and **keeps the compiled template in memory** |

!!! tip "The cached loader in production"
    By default, with `APP_DIRS: True` Django already uses `app_directories` +
    `filesystem`. In production, the **cached loader** compiles each template
    once and reuses it — a real performance win. Configure it explicitly in
    `OPTIONS` with `loaders` when you want to control this (don't combine
    `loaders` with `APP_DIRS` in the same engine).

### Where the templates live (finder recap)

- `templates/` at the project root (via `DIRS`).
- `<app>/templates/<app>/` in each app (via `APP_DIRS`), where the same-named
  subdirectory creates the namespace (`blog/post_list.html`).

For the DTL content itself — tags, filters, inheritance — see
**[Templates](templates.md)**.

!!! quote "📖 In the official docs"
    - [Templates](https://docs.djangoproject.com/en/stable/topics/templates/)
    - [The templates API (backends)](https://docs.djangoproject.com/en/stable/ref/templates/api/)

## Recap

- A **template engine** renders the HTML; the `TEMPLATES` setting is a list of
  engines, each with its own `BACKEND`.
- **DTL** (default, integrates everything, logic limited on purpose) × **Jinja2**
  (more powerful and faster, but you re-expose `url`/`static`/`csrf` by hand).
- You can use both; Django tries them in order.
- **Loaders** (`app_directories`, `filesystem`, `cached`) define where/how to
  find the files; `APP_DIRS: True` turns on the search inside apps; `cached`
  speeds things up in production.
- Rule of thumb: stick with the DTL unless you have a strong reason not to.

For the DTL language in detail, head over to **[Templates](templates.md)**.
