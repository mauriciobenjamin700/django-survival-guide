# Setting up the project

Before writing any feature, we need to understand **how a Django project is
organized**. Django separates two concepts:

- **Project** — the overall configuration (settings, root URLs, WSGI/ASGI).
- **App** — a module with one responsibility (here, the `blog`).

A project contains several apps. Each app should do *one* thing well.

## The structure we use

```text
example/
├── manage.py                 # ponto de entrada dos comandos
├── config/                   # o "projeto": configuração geral
│   ├── settings.py           # todas as configurações
│   ├── urls.py               # roteamento raiz
│   ├── wsgi.py / asgi.py     # servidores de produção
└── apps/
    └── blog/                 # o "app": nossa funcionalidade
        ├── apps.py           # configuração do app
        ├── models.py         # tabelas do banco
        ├── views.py          # lógica de requisição/resposta
        ├── urls.py           # rotas do app
        ├── forms.py          # formulários
        ├── admin.py          # configuração do admin
        └── templates/        # HTML
```

!!! info "Why an `apps/` folder?"
    `startproject` generates apps at the root by default. Placing them under `apps/`
    keeps the root clean and makes it clear what is *your code* versus configuration.
    It's a common convention in larger projects.

## How we created it

```bash
uv run django-admin startproject config .
mkdir -p apps/blog
uv run python manage.py startapp blog apps/blog
```

## `settings.py` — no magic

`settings.py` is just a **Python module with module-level variables** that
Django reads on startup. No special format. Here's how we make the values
environment-sensitive, with friendly defaults for development:

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

!!! tip "Typing in settings"
    Annotating `BASE_DIR: Path`, `DEBUG: bool`, etc. doesn't change the behavior, but
    it documents the expected type and helps the editor. It's our principle of *clear
    typing* applied even to configuration.

!!! warning "`SECRET_KEY` and `DEBUG` in production"
    Never use the default `SECRET_KEY` in production, and always run with `DEBUG=false`.
    That's why we read both from environment variables: in production you set
    `DJANGO_SECRET_KEY` and `DJANGO_DEBUG=false` without touching the code.

### Registering the app

For Django to "see" the blog, it goes into `INSTALLED_APPS`:

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

Since the app is in `apps/blog/`, `apps.py` declares the path and a short
`label` so the tables don't end up with a giant name:

```python
from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field: str = "django.db.models.BigAutoField"
    name: str = "apps.blog"   # caminho de importação
    label: str = "blog"       # tabelas viram blog_post, blog_tag...
```

!!! note "`name` vs `label`"
    - `name` is the **import path** (`apps.blog`) — it must match the
      real folder.
    - `label` is the **internal alias** used in table names and migrations. Without
      it, the tables would be `apps_blog_post` instead of `blog_post`.

## `manage.py`

It's the project's Swiss Army knife. Every administrative command goes through it:

```bash
uv run python manage.py <comando>
```

Some we'll use right away: `migrate`, `makemigrations`, `runserver`,
`createsuperuser`, `shell`, `test`.

## Recap

- A **project** (`config/`) gathers configuration; an **app** (`apps/blog/`)
  gathers a feature.
- `settings.py` is pure Python — module variables, which we type and make
  environment-sensitive.
- An app only exists for Django if it's in `INSTALLED_APPS`.
- `name` is the import path; `label` is the tables' short alias.

Now that the skeleton is standing, let's model the data in
**[Models and the ORM](models.md)**.
