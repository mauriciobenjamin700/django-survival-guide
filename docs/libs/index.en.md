# Ecosystem libraries

Django does a lot on its own, but the community has built libraries that solve
common problems without you reinventing the wheel: social login, background
tasks, real time, API filtering. This section covers the most widely used ones.

!!! quote "Think like a child 🧒"
    Django is a huge box of Lego. The libraries are ready-made **special pieces** —
    a wheel that already spins, a door that already opens. You snap them in instead of
    carving from scratch. But every extra piece is one more piece to **maintain** —
    so choose carefully.

## The map of this section

| Library | Solves |
| --- | --- |
| [django-allauth](allauth.md) | Sign-up, login (including social), email verification |
| [Celery](celery.md) | Background and scheduled tasks (outside the request) |
| [Django Channels](channels.md) | WebSockets and real time (chat, notifications) |
| [SSE — Server-Sent Events](sse.md) | One-way real time (server → client) |
| [Web Push](webpush.md) | Notifications even when the site is closed |
| [django-filter](django-filter.md) | Filtering listings and APIs by query params |
| [Friends (catalog)](afins.md) | debug-toolbar, extensions, environ, CORS, JWT, OpenAPI... |
| [Containerized services](containers.md) | Postgres, Redis, RabbitMQ, MinIO, Flower via compose |

## How to choose (and add) a library

Before installing anything, ask:

1. **Does Django already do this?** Lots of people install a lib for what already exists natively
   (auth, cache, sessions). Check the [Reference](../referencia/index.md) first.
2. **Is the lib maintained?** Check on GitHub: recent commits, issues being answered,
   compatibility with your Django version. An abandoned lib becomes debt.
3. **Is it worth the cost?** Every dependency is more surface to update, break and
   audit. Big libraries (Celery, Channels) change the project's architecture.

!!! tip "The ritual of adding a Django lib"
    Most follow the same step-by-step:
    ```bash
    uv add lib-name
    ```
    ```python
    # settings.py
    INSTALLED_APPS = [
        # ...
        "the_lib",            # (1) register the app
    ]
    ```
    ```python
    # urls.py (if the lib exposes routes)
    path("prefix/", include("the_lib.urls")),
    ```
    ```bash
    python manage.py migrate   # (2) if the lib has models
    ```
    Install → register in `INSTALLED_APPS` → (routes) → `migrate`. Keep this
    rhythm in mind; it repeats on almost every page in this section.

!!! warning "Pin versions and read the changelog when upgrading"
    `uv.lock` already pins the versions. When bumping a lib to a major version (e.g. Celery
    5→6), **read the changelog** — infrastructure libs frequently break compatibility
    across major versions.

## Recap

- Libraries snap in ready-made solutions; each one is also maintenance.
- Before installing: does Django already do it? is the lib maintained? is the cost worth it?
- The ritual: `uv add` → `INSTALLED_APPS` → routes (if any) → `migrate`.
- Pin versions (`uv.lock`) and read changelogs on major upgrades.

Start with the one almost every project needs: supercharged authentication with
**[django-allauth](allauth.md)**.
