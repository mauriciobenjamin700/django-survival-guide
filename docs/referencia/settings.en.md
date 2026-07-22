# Reference: settings

!!! quote "Think like a child 🧒"
    The `settings.py` is the **panel of buttons** for the whole project: where the
    database lives, which "parts" (apps) are switched on, whether test mode is lit
    up. There's no magic — it's just a Python file with variables. When Django wakes
    up, it reads this panel and configures itself.

## Use case

You want the same code running in two places: on your PC (a simple database,
detailed errors) and in production (a real database, secure). The solution is to
read the sensitive values from the **environment**, with dev-friendly defaults:

```python
# config/settings.py
import os
from pathlib import Path

BASE_DIR: Path = Path(__file__).resolve().parent.parent

SECRET_KEY: str = os.environ.get("DJANGO_SECRET_KEY", "dev-only-change-me")
DEBUG: bool = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS: list[str] = os.environ.get(
    "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1"
).split(",")
```

On your PC, it runs without configuring anything. In production, you set the
environment variables and nothing in the code changes. Let's go to the full panel.

## Possibilities

### The settings you touch the most

| Setting | What it controls |
| --- | --- |
| `SECRET_KEY` | Secret key (signatures, sessions). Absolute secret |
| `DEBUG` | `True` shows detailed errors. **Always `False` in production** |
| `ALLOWED_HOSTS` | Domains that may serve the site |
| `INSTALLED_APPS` | Apps switched on (yours + Django's + third-party) |
| `MIDDLEWARE` | Layers that wrap each request (order matters!) |
| `DATABASES` | Connection(s) to the database |
| `TEMPLATES` | Where and how to find templates |
| `STATIC_URL` / `STATIC_ROOT` | Static files (CSS/JS/images) |
| `MEDIA_URL` / `MEDIA_ROOT` | Files uploaded by users |
| `LANGUAGE_CODE` / `TIME_ZONE` | Language and time zone |
| `USE_I18N` / `USE_TZ` | Translations on / dates with time zone |
| `DEFAULT_AUTO_FIELD` | Type of the automatic PK |
| `AUTH_USER_MODEL` | The project's user model |
| `LOGIN_URL` / `LOGIN_REDIRECT_URL` | Login routes |

!!! danger "The security tripod: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`"
    In production: `SECRET_KEY` comes from the environment (never in Git),
    `DEBUG=False` (otherwise you leak stack traces with sensitive data), and
    `ALLOWED_HOSTS` lists only your domains. Run `python manage.py check --deploy`
    for it to point out what's missing.

### `DATABASES`: dev × production

```python
# development: SQLite (one file, zero configuration)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# production: PostgreSQL via the environment
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["DB_NAME"],
        "USER": os.environ["DB_USER"],
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}
```

### `MIDDLEWARE`: the order is an onion

Think like a child: each middleware is an **onion layer** around the view. The
request comes in crossing the layers from outside in; the response goes out from
inside out. Changing the order changes the behavior.

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",   # gives you request.user
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

!!! warning "Don't reorder without knowing"
    `AuthenticationMiddleware` needs to come **after** `SessionMiddleware` (it reads
    the session to find the user). The default order from `startproject` is
    correct — only touch it with a reason.

### Organization patterns

As `settings.py` grows, there are three common approaches:

=== "One file + environment (the one in the example)"

    A single `settings.py`, reading what varies from `os.environ`. Simple and
    enough for most projects.

=== "A `settings/` package per environment"

    ```text
    config/settings/
    ├── base.py        # common
    ├── dev.py         # from .base import *  (+ overrides)
    └── prod.py        # from .base import *  (+ overrides)
    ```
    You pick via `DJANGO_SETTINGS_MODULE=config.settings.prod`.

=== "A library (django-environ)"

    Reads a `.env` file and converts types (`env.bool`, `env.db`). Reduces the
    `os.environ` boilerplate.

!!! tip "Typing the settings helps"
    Annotating `DEBUG: bool`, `ALLOWED_HOSTS: list[str]` doesn't change the
    behavior, but it documents the expected format and the editor keeps up with
    you. It's our principle of clear typing, even in the configuration.

### `manage.py` and `DJANGO_SETTINGS_MODULE`

Django figures out which settings to use from the environment variable
`DJANGO_SETTINGS_MODULE`. The `manage.py` sets it for you in development:

```python
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
```

In production, the server (Gunicorn/Uvicorn) sets it pointing to the production
module.

## Recap

- `settings.py` is pure Python — variables Django reads at startup.
- Read what varies from the **environment** (`os.environ`) with dev defaults; the
  same code runs anywhere.
- Security tripod: `SECRET_KEY` (from the environment), `DEBUG=False` in
  production, restricted `ALLOWED_HOSTS`. Validate with `check --deploy`.
- `DATABASES` swaps SQLite (dev) for PostgreSQL (prod); `MIDDLEWARE` is an onion
  where the order matters.
- Organize with one file + env, a package per environment, or `django-environ`.

One of the most important apps comes switched on by default: the users one. See
**[authentication and permissions](auth.md)**.
