# Configuration, environments and secrets (12-factor)

!!! quote "Think like a child 🧒"
    The cake recipe is always the same (the **code**). But the amount of sugar
    changes: at your house you add a lot, at diabetic grandma's house you add
    none. The **environment** is the kitchen where the cake is baked, and the
    **secrets** are the secret ingredients you never write on a piece of paper
    that anyone can read. The recipe goes in the notebook (Git); the sugar and
    the secret ingredient stay in the kitchen (environment variables).

## Use case

You have a `settings.py` and, without thinking, wrote this:

```python
SECRET_KEY = "django-insecure-l9$k2m..."
DEBUG = True
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "blog",
        "USER": "postgres",
        "PASSWORD": "supersecret123",
        "HOST": "localhost",
    }
}
```

Then you ran `git push`. Done: your database password and your `SECRET_KEY` are
in the repository history **forever**, and `DEBUG = True` goes to production
showing stack traces to the world. The right way is to read all of this from the
**environment**:

```python
import os

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["DB_NAME"],
        "USER": os.environ["DB_USER"],
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": os.environ.get("DB_HOST", "localhost"),
    }
}
```

The code no longer knows any password. It only knows "read `DB_PASSWORD` from
wherever you are running". This is the
**[12-factor](https://12factor.net/config)** way: **config lives in the
environment, not in the code.**

## Possibilities

### Why separate config from code?

The 12-factor manifesto has a golden rule (Factor III): you should be able to
make your repository **public right now** without leaking any secrets. If you
can't, it's because there's config hidden in the code.

| Goes in Git (code) | Does NOT go in Git (environment) |
| --- | --- |
| `INSTALLED_APPS` structure, middleware, `ROOT_URLCONF` | `SECRET_KEY` |
| Logical names ("there is a `default` database") | Database password, user and host |
| Safe defaults (`DEBUG = False`) | API keys (Stripe, AWS, email) |
| `.env.example` (just the variable names) | `.env` (the real values) |

!!! danger "Never commit `SECRET_KEY`, passwords or the `.env` file"
    If a secret was already committed, changing the value isn't enough: it stays
    in the history. You need to **rotate** it (generate a new secret) and revoke
    the old one. Prevention is far cheaper: add `.env` to `.gitignore` on day
    one.

### Reading variables: plain `os.environ`

The simplest way, with no dependency at all. The important detail is the
difference between `[]` and `.get()`:

```python
import os

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]        # (1)!
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"  # (2)!
```

1. `os.environ["X"]` **blows up** with `KeyError` if the variable doesn't exist.
    Use it for required secrets: better the app doesn't start than starts
    insecure.
2. `os.environ.get("X", default)` returns the default when missing. Use it for
    optional config.

!!! warning "An environment variable is always a string"
    `os.environ` only delivers text. `DEBUG=True` in the shell becomes the
    string `"True"`, and the string `"False"` is **truthy** in Python (any
    non-empty string is truthy). That's why we compare with `== "True"`. For
    numbers use `int(os.environ["PORT"])`. This is where a casting library helps.

### Reading variables: `django-environ` (recommended)

`django-environ` solves type casting and even understands database URLs. It's
the option most Django projects use.

```bash
uv add django-environ
```

```python
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),          # (1)!
    ALLOWED_HOSTS=(list, ["127.0.0.1"]),
)
environ.Env.read_env(BASE_DIR / ".env")  # (2)!

SECRET_KEY = env("DJANGO_SECRET_KEY")            # required: no default
DEBUG = env("DJANGO_DEBUG")                      # already a real bool
ALLOWED_HOSTS = env("ALLOWED_HOSTS")             # already a list

DATABASES = {
    "default": env.db("DATABASE_URL"),           # (3)!
}
```

1. You declare the **type** and the **default** of each variable once. Then
    `env("X")` already returns the right type (bool, int, list...), with no
    manual `== "True"`.
2. `read_env()` loads the `.env` file into `os.environ`. In production you
    usually **don't** have a `.env`: the variables already come from the real
    environment, and this line simply doesn't find the file and moves on.
3. `env.db()` parses a URL like `postgres://user:secret@host:5432/blog` into the
    dict Django expects. One variable instead of five.

| Method | Reads | Example value |
| --- | --- | --- |
| `env("X")` | string | `abc` |
| `env.bool("X")` | boolean | `True` / `False` |
| `env.int("X")` | integer | `5432` |
| `env.list("X")` | list (comma-separated) | `a,b,c` |
| `env.db("DATABASE_URL")` | database connection dict | `postgres://...` |
| `env.cache("CACHE_URL")` | cache dict | `redis://...` |

### The `.env` + `.env.example` pair

Two files that travel together:

- **`.env`** — the **real** values (with secrets). Lives in `.gitignore`, never
  in Git. Each dev/server has its own.
- **`.env.example`** — just the variable **names**, with fake or empty values.
  It **does** go in Git. It's the documentation of "what I need to configure to
  run this".

`.env` (on your machine, secret):

```bash
DJANGO_SECRET_KEY=a-real-long-and-random-key
DJANGO_DEBUG=True
DATABASE_URL=postgres://postgres:supersecret123@localhost:5432/blog
ALLOWED_HOSTS=127.0.0.1,localhost
```

`.env.example` (goes to Git, no secrets):

```bash
DJANGO_SECRET_KEY=
DJANGO_DEBUG=False
DATABASE_URL=postgres://user:password@localhost:5432/dbname
ALLOWED_HOSTS=127.0.0.1,localhost
```

`.gitignore`:

```bash
.env
*.env
!.env.example
```

!!! tip "Generating a fresh `SECRET_KEY`"
    Never reuse the key `startproject` generated (it carries the
    `django-insecure-` prefix on purpose). Generate one for production:
    ```bash
    python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
    ```
    Paste the result into the server's `.env`, never into the code.

### Choosing settings: `DJANGO_SETTINGS_MODULE`

Django needs to know **which** settings module to use. That comes from the
environment variable `DJANGO_SETTINGS_MODULE`, which `manage.py` and
`wsgi.py`/`asgi.py` set with a default:

```python
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
```

`setdefault` only sets it if it doesn't exist yet — so in production you
**override** it by exporting another:

```bash
export DJANGO_SETTINGS_MODULE=config.settings.prod
python manage.py migrate
```

There are two strategies to handle multiple environments. Pick one:

### Strategy A: single file driven by env

A single `settings.py`, and `if`s decide based on the environment. Simple, great
for small and medium projects.

```python
import environ

env = environ.Env(DJANGO_DEBUG=(bool, False))

DEBUG = env("DJANGO_DEBUG")

if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

- **Pros:** one file, easy to follow, no import magic.
- **Cons:** it can become a soup of `if`s if the environments diverge a lot.

### Strategy B: split settings

Turn `settings.py` into a `settings/` **package** with a common part and one per
environment:

```text
config/
└── settings/
    ├── __init__.py
    ├── base.py      # everything common
    ├── dev.py       # from .base import *  (+ dev tweaks)
    ├── prod.py      # from .base import *  (+ prod tweaks)
    └── test.py      # from .base import *  (+ test tweaks)
```

`base.py` (the common trunk):

```python
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.blog",
]

ROOT_URLCONF = "config.urls"
```

`dev.py` (inherits everything and tweaks):

```python
from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

`prod.py` (inherits everything and hardens):

```python
from .base import *  # noqa: F403

DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")  # noqa: F405

DATABASES = {"default": env.db("DATABASE_URL")}  # noqa: F405

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

And you select the environment through the variable:

```bash
export DJANGO_SETTINGS_MODULE=config.settings.prod
```

!!! note "`from .base import *` is the exception to the imports rule"
    In application code we avoid `import *`. In split settings it's the
    **idiomatic pattern**: settings are just module variables, and the goal is
    precisely to pull all of them from `base` into the environment file. The
    `# noqa` markers silence the linter, which would complain about "undefined"
    names coming from the `*`.

```mermaid
flowchart TD
    ENV["DJANGO_SETTINGS_MODULE"] -->|config.settings.dev| DEV["dev.py"]
    ENV -->|config.settings.prod| PROD["prod.py"]
    ENV -->|config.settings.test| TEST["test.py"]
    DEV --> BASE["base.py<br/>(common config)"]
    PROD --> BASE
    TEST --> BASE
```

!!! tip "Strategy A vs. B — which to choose?"
    Start with **A** (single file + env). Move to **B** when the environments
    start to truly diverge (different backends, dev-only apps like
    `debug_toolbar`, etc.). There's no universal "right" — there's what keeps
    your `settings` readable for your project size.

### Dependencies per environment

Just like config, **dependencies** change per environment: `pytest` and
`django-debug-toolbar` have no reason to go to production. With `uv` you use
dependency groups:

```bash
uv add django django-environ psycopg          # runs in production
uv add --group dev pytest-django ruff django-debug-toolbar  # development only
```

This writes to `pyproject.toml`:

```toml
[project]
dependencies = [
    "django>=6.0",
    "django-environ>=0.11",
    "psycopg>=3.2",
]

[dependency-groups]
dev = [
    "pytest-django>=4.9",
    "ruff>=0.9",
    "django-debug-toolbar>=4.4",
]
```

On the server you install **only** what production needs:

```bash
uv sync --no-dev
```

!!! info "`debug_toolbar` only enters in dev"
    Apps that exist only in development should enter `INSTALLED_APPS` only in
    `dev.py` (or inside an `if DEBUG:` in strategy A). Putting them in `base.py`
    would make production try to import a package you didn't even install with
    `--no-dev`.

### Project structure that scales: an `apps/` folder

When the project grows, dumping every app at the root becomes a mess. Group the
apps into an `apps/` folder, each one with **a single responsibility**:

```text
myproject/
├── manage.py
├── pyproject.toml
├── .env.example
├── .gitignore
├── config/                 # the Django "project" (settings, urls, wsgi)
│   ├── __init__.py
│   ├── settings/
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
└── apps/                   # your domain apps
    ├── __init__.py
    ├── blog/
    │   ├── __init__.py
    │   ├── apps.py
    │   ├── models.py
    │   ├── views.py
    │   └── urls.py
    └── accounts/
        └── ...
```

For Django to find `apps.blog`, reference it with the full path in
`INSTALLED_APPS` and in the `AppConfig`:

```python
# apps/blog/apps.py
from django.apps import AppConfig


class BlogConfig(AppConfig):
    """Configuration for the blog app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.blog"
```

```python
# config/settings/base.py
INSTALLED_APPS = [
    "django.contrib.admin",
    # ...
    "apps.blog",
    "apps.accounts",
]
```

!!! tip "One app, one responsibility"
    Ask "could I rip this app out and use it in another project?". `blog`,
    `accounts`, `payments` are good apps: cohesive and focused. A giant app
    called `core` that does everything is the opposite smell. Small, reusable
    apps are the heart of Django's philosophy.

!!! quote "📖 In the official docs"
    - [Django settings](https://docs.djangoproject.com/en/6.0/topics/settings/)
    - [django-environ](https://django-environ.readthedocs.io/)
    - [The Twelve-Factor App — Config](https://12factor.net/config)

## Recap

- **Config lives in the environment, not in the code** (12-factor): you should
  be able to make the repo public without leaking anything.
- Never commit `SECRET_KEY`, passwords or `.env`. If it leaked, **rotate** it —
  changing the value doesn't erase the history.
- Read variables with `os.environ` (remember: everything is a string) or, better,
  with `django-environ` (type casting + `env.db()` for free).
- `.env` (real values, in `.gitignore`) travels alongside `.env.example` (just
  the names, in Git).
- `DJANGO_SETTINGS_MODULE` chooses the settings module; `setdefault` in
  `manage.py`, `export` in production.
- Two patterns: **single file driven by env** (start here) or **split settings**
  (`base`/`dev`/`prod`/`test` with `from .base import *`).
- Dependencies per environment with `uv` groups (`--group dev`); in production,
  `uv sync --no-dev`.
- Scale with an `apps/` folder, one app per responsibility.

Want to see each settings key in detail? Head to the
**[settings reference](settings.md)**.
