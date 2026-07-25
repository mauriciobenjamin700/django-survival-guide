# Setting up the project

!!! info "Starting point"
    This page picks up where **[Installation](../get-started/installation.md)**
    left off: you already have a folder with `manage.py`, `config/`, and the
    server starting up. If you don't yet, do that page first — it takes a few
    minutes.

Before writing any feature, we need to understand **how a Django project is
organized**. Django separates two concepts:

- **Project** — the overall configuration (settings, root URLs, WSGI/ASGI).
- **App** — a module with one responsibility (here, the `blog`).

A project contains several apps. Each app should do *one* thing well.

## The structure we'll build

```text
my-blog/                      # (in the guide's repository: example/)
├── manage.py                 # entry point for every command
├── config/                   # the "project": overall configuration
│   ├── settings.py           # all the settings
│   ├── urls.py               # root routing
│   ├── wsgi.py / asgi.py     # production servers
└── apps/
    └── blog/                 # the "app": our feature
        ├── apps.py           # app configuration
        ├── models.py         # database tables
        ├── views.py          # request/response logic
        ├── urls.py           # app routes
        ├── forms.py          # forms
        ├── admin.py          # admin configuration
        └── templates/        # HTML
```

!!! info "Why an `apps/` folder?"
    `startproject` generates apps at the root by default. Placing them under `apps/`
    keeps the root clean and makes it clear what is *your code* versus configuration.
    It's a common convention in larger projects.

## Creating the `blog` app

You already created `config/` during Installation
(`django-admin startproject config .`). Now create the app, inside your project
folder:

```bash
mkdir -p apps/blog
touch apps/__init__.py
uv run python manage.py startapp blog apps/blog
```

Line by line:

1. `mkdir -p apps/blog` — `startapp` **does not create** the target folder; it
   has to exist beforehand.
2. `touch apps/__init__.py` — turns `apps/` into an explicit **Python package**.
3. `startapp blog apps/blog` — generates the app skeleton *inside* `apps/blog`.

??? info "Is `__init__.py` really required?"
    Technically no: since Python 3.3 there are *namespace packages*, and
    `import apps.blog` works even without the file. We create it anyway because
    an explicit package makes the intent clear and avoids odd behavior in build,
    packaging, and test-discovery tools.

!!! warning "Windows"
    `mkdir -p` and `touch` are Unix commands. In PowerShell:
    ```powershell
    mkdir apps\blog
    New-Item apps\__init__.py
    uv run python manage.py startapp blog apps\blog
    ```

The result:

```text
apps/
├── __init__.py
└── blog/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── migrations/
    ├── models.py
    ├── tests.py
    └── views.py
```

!!! note "No `urls.py`, `forms.py`, or `templates/`?"
    Correct — `startapp` doesn't generate those. You create each one when the
    matching tutorial page needs it. No leftover empty files.

## `settings.py` — no magic

`settings.py` is just a **Python module with module-level variables** that
Django reads on startup. No special format.

Open `config/settings.py`. `startproject` left the `SECRET_KEY` hardcoded and
`DEBUG = True` nailed down. Change those lines to read from the environment,
with friendly defaults for development:

```python
import os
from pathlib import Path

BASE_DIR: Path = Path(__file__).resolve().parent.parent

SECRET_KEY: str = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-only-change-me-in-production",
)

DEBUG: bool = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"

ALLOWED_HOSTS: list[str] = os.environ.get(
    "DJANGO_ALLOWED_HOSTS",
    "localhost,127.0.0.1",
).split(",")
```

!!! note "Single quotes in the generated file"
    `startproject` writes everything with single quotes
    (`'django.contrib.admin'`). In this guide we standardize on **double
    quotes** — pure style, Python treats both the same. To normalize the whole
    file at once, [ruff](../sobre/lint.md) does it with `ruff format`.

!!! tip "Typing in settings"
    Annotating `BASE_DIR: Path`, `DEBUG: bool`, etc. doesn't change the behavior, but
    it documents the expected type and helps the editor. It's our principle of *clear
    typing* applied even to configuration.

!!! warning "`SECRET_KEY` and `DEBUG` in production"
    Never use the default `SECRET_KEY` in production, and always run with `DEBUG=false`.
    That's why we read both from environment variables: in production you set
    `DJANGO_SECRET_KEY` and `DJANGO_DEBUG=false` without touching the code.

### Registering the app

For Django to "see" the blog, it goes into `INSTALLED_APPS` — still in
`config/settings.py`, add the last line:

```python
INSTALLED_APPS: list[str] = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.blog",  # (1)!
]
```

1. Note the path `apps.blog`: it's the real Python import path, because the
   app lives in `apps/blog/`.

That alone isn't enough yet. `startapp` generated `apps/blog/apps.py` with
`name = "blog"` — the **wrong** path, because the app isn't at the root. Edit
the file to declare the real path and a short `label`, so the tables don't end
up with a giant name:

```python
from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field: str = "django.db.models.BigAutoField"  # (1)!
    name: str = "apps.blog"                                    # (2)!
    label: str = "blog"                                        # (3)!
```

1. The type of the **automatic primary key** — explained right below.
2. The app's **import path**.
3. The **internal alias**: tables become `blog_post`, `blog_tag`...

!!! note "`name` vs `label`"
    - `name` is the **import path** (`apps.blog`) — it must match the
      real folder.
    - `label` is the **internal alias** used in table names and migrations. Without
      it, the tables would be `apps_blog_post` instead of `blog_post`.

### What `default_auto_field` is for

Every table needs a **primary key** (the column that identifies each row — the
`id`). You almost never declare it: Django creates it for you. This line says
**which type** it creates.

!!! quote "Think like a child 🧒"
    It's the **ticket dispenser at the deli counter**: everyone who walks in gets
    the next number, and no number repeats. `default_auto_field` only picks **what
    kind of ticket** the machine prints.

With `BigAutoField` you get a 64-bit integer the database increments on every
`INSERT` — `1, 2, 3, ...`. Details worth knowing:

- It applies to the models of **this app** that don't declare `primary_key` — and
  it's the default `startapp` already writes.
- Delete the line and Django falls back to `DEFAULT_AUTO_FIELD` in `settings.py`
  (which `startproject` already sets to `BigAutoField`). With neither, you get the
  32-bit `AutoField` — which runs out at ~2.1 billion rows.
- Changing the value **after** tables exist generates a migration (`ALTER
  COLUMN`), and on a big table that's slow. Decide early.

??? question "What if I want a UUID primary key?"
    Natural temptation: swap this line for a UUID. It **doesn't work** — not even
    with a field of your own:

    ```python
    class BlogConfig(AppConfig):
        default_auto_field: str = "apps.blog.fields.UUIDAutoField"
    ```

    ```text
    ValueError: Primary key 'apps.blog.fields.UUIDAutoField' referred by
    apps.blog.apps.BlogConfig.default_auto_field must subclass AutoField.
    ```

    Django requires the field to be an `AutoField` subclass (the `AutoFieldMeta`
    metaclass only accepts `BigAutoField`, `SmallAutoField` or real subclasses) —
    and `UUIDField` isn't one. Django's own source comment says a **non-integer**
    automatic field will only be possible once the value can come from a database
    default.

    The right path is declaring the PK **on the model**, usually on an abstract
    model so you don't repeat yourself:

    ```python
    # apps/blog/models.py
    import uuid

    from django.db import models


    class BaseModel(models.Model):
        """Abstract base with a UUID primary key."""

        id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

        class Meta:
            abstract = True


    class Post(BaseModel):
        title = models.CharField(max_length=200)
    ```

    And `default_auto_field` **still matters**: the tables Django creates on its
    own (a `ManyToManyField`'s join table, for instance) keep using it. With the
    models above, `blog_post` has a UUID `id`, but `blog_post_tags` has an integer
    one — the two coexist.

    What changes elsewhere if you adopt UUIDs: routes switch to `<uuid:pk>`
    instead of `<int:pk>`, `seed`/fixtures can no longer assume `id=1`, and every
    FK grows from 8 to 16 bytes.

    | | `BigAutoField` | `UUIDField` |
    | --- | --- | --- |
    | Size | 8 bytes | 16 bytes (32 chars on SQLite) |
    | Who generates it | the database, on `INSERT` | the app, before the `INSERT` |
    | Order | ascending by insertion | random (v4) → index fragments |
    | In the URL | `/posts/42/` — enumerable | `/posts/1fb72e6d-…/` — opaque |
    | Merging databases | collides | doesn't collide |

    !!! tip "UUIDv7 fixes the fragmentation"
        v4 is random, so every `INSERT` lands anywhere in the index. **v7** embeds
        the timestamp up front, making it ascending again. On Python **3.14+** use
        `uuid.uuid7`; before that, the [`uuid6`](https://pypi.org/project/uuid6/)
        library.

    **This guide sticks with `BigAutoField`** — it's Django's default, cheaper on
    indexes and plenty for a blog. Go UUID when the id is publicly exposed or when
    several databases will be merged.

## `manage.py`

It's the project's Swiss Army knife. Every administrative command goes through it:

```bash
uv run python manage.py <command>
```

Some we'll use right away: `migrate`, `makemigrations`, `runserver`,
`createsuperuser`, `shell`, `test`.

## Checking that it stands up

```bash
uv run python manage.py check
```

It should answer `System check identified no issues (0 silenced).`

!!! failure "`ImproperlyConfigured: Cannot import 'blog'`"
    Full message:
    ```text
    django.core.exceptions.ImproperlyConfigured: Cannot import 'blog'.
    Check that 'apps.blog.apps.BlogConfig.name' is correct.
    ```
    The `name` in `apps/blog/apps.py` is still `"blog"` (what `startapp`
    generated) instead of `"apps.blog"`. That's exactly the fix from the
    previous section.

!!! quote "📖 In the official docs"
    - [Applications](https://docs.djangoproject.com/en/stable/ref/applications/)

## Recap

- A **project** (`config/`) gathers configuration; an **app** (`apps/blog/`)
  gathers a feature.
- `settings.py` is pure Python — module variables, which we type and make
  environment-sensitive.
- An app only exists for Django if it's in `INSTALLED_APPS`.
- `name` is the import path; `label` is the tables' short alias.
- `manage.py check` is the quick way to validate the configuration before moving
  on.

Now that the skeleton is standing, let's model the data in
**[Models and the ORM](models.md)**.
