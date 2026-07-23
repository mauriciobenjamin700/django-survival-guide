# Reference: deploy with Docker Compose

!!! quote "Think like a child 🧒"
    Taking the app to production is like moving house with several pieces of
    furniture: Django, the database, the files. **Docker** puts each piece of
    furniture in a **sealed box** (container) that works the same anywhere. **Docker
    Compose** is the moving list: "I want a box for the app and a box for the
    database, and they talk to each other like this". You give one command and the
    whole house comes up assembled.

## Use case

You want to bring the blog up in production with **PostgreSQL**, migrations
applied and static files served — all with one command:

```bash
docker compose up -d --build
```

That brings up two containers: the database (`db`) and the app (`web`). The app
waits for the database to become healthy, runs `migrate` and `collectstatic`, and
serves with **Gunicorn**. Open <http://localhost:8000/>. For sample data:

```bash
docker compose exec web python manage.py seed_blog
```

!!! check "This actually runs"
    The files [`Dockerfile`](https://github.com/mauriciobenjamin700/django-survival-guide/blob/main/Dockerfile),
    [`docker-compose.yml`](https://github.com/mauriciobenjamin700/django-survival-guide/blob/main/docker-compose.yml)
    and [`docker/entrypoint.sh`](https://github.com/mauriciobenjamin700/django-survival-guide/blob/main/docker/entrypoint.sh)
    are in the repository and were tested by bringing the full stack up.

## What's possible

### The `Dockerfile`: the recipe for the app's box

```dockerfile
# syntax=docker/dockerfile:1

FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv   # (1)!

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --group prod --no-install-project   # (2)!

COPY example/ ./example/
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /app/example

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
```

1. Copies the `uv` binary from an official image — installs dependencies fast.
2. Installs **only** what's needed for production: `--no-dev` (no pytest/mkdocs) and
    `--group prod` (gunicorn, whitenoise, psycopg). `--frozen` respects the
    `uv.lock`.

!!! tip "Layers: copy the lock BEFORE the code"
    Copying `pyproject.toml`/`uv.lock` and installing **before** copying `example/`
    makes Docker cache the dependency layer. Changed only the code? The rebuild
    doesn't reinstall everything. Think like a child: put the heavy toys at the
    bottom of the backpack; you don't take them out every time.

### The `entrypoint.sh`: what runs when the box opens

```sh
#!/bin/sh
set -e

python manage.py migrate --no-input
python manage.py collectstatic --no-input

exec "$@"
```

- Applies migrations and collects static files **every time** the container comes
  up.
- `exec "$@"` hands control to the `CMD` (the Gunicorn) — without leaving an extra
  process hanging around.

!!! warning "Auto-migration on start: good to begin with, careful when scaling"
    Running `migrate` in the entrypoint is great for 1 instance. With **several**
    replicas coming up together, they'd all try to migrate at the same time. Then
    move the `migrate` to a separate deploy step (a job/`docker compose run web
    python manage.py migrate`) before bringing up the replicas.

### The `docker-compose.yml`: the moving list

```yaml
services:
  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: blog
      POSTGRES_USER: blog
      POSTGRES_PASSWORD: blog
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U blog"]
      interval: 5s
      timeout: 3s
      retries: 5

  web:
    build: .
    environment:
      DJANGO_DEBUG: "false"
      DJANGO_SECRET_KEY: "change-me-in-production"
      DJANGO_ALLOWED_HOSTS: "localhost,127.0.0.1"
      DJANGO_DB_NAME: blog
      DJANGO_DB_USER: blog
      DJANGO_DB_PASSWORD: blog
      DJANGO_DB_HOST: db          # (1)!
      DJANGO_DB_PORT: "5432"
    volumes:
      - media:/app/example/media   # (2)!
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy  # (3)!

volumes:
  pgdata:
  media:
```

1. The database host is **`db`** — the service name. In Compose, containers find
    each other by the service name, as if it were an internal DNS.
2. A **volume** so the uploads survive container rebuilds.
3. `web` only comes up **after** `db` passes the `healthcheck` — without it, the
    app would try to connect before the database was ready.

### How `settings.py` reacts to the environment

The same code runs on SQLite (dev) or Postgres (Docker) because the `settings`
**reads the environment**:

```python
if os.environ.get("DJANGO_DB_NAME"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["DJANGO_DB_NAME"],
            "USER": os.environ.get("DJANGO_DB_USER", "postgres"),
            "PASSWORD": os.environ.get("DJANGO_DB_PASSWORD", ""),
            "HOST": os.environ.get("DJANGO_DB_HOST", "localhost"),
            "PORT": os.environ.get("DJANGO_DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
```

And the static files are served by **WhiteNoise** (no need for Nginx for the
basics):

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",   # right after security
    # ...
]
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
```

### Day-to-day commands

| Command | Does |
| --- | --- |
| `docker compose up -d --build` | Brings everything up (rebuilds the image) |
| `docker compose logs -f web` | Follows the app's logs |
| `docker compose exec web python manage.py seed_blog` | Runs a command inside the app |
| `docker compose exec web python manage.py createsuperuser` | Creates an admin |
| `docker compose ps` | Shows the state of the services |
| `docker compose down` | Tears it down (keeps the volumes) |
| `docker compose down -v` | Tears it down **and deletes** the volumes (data!) |

### `.dockerignore`: don't package junk

```text
.git
.venv
*.sqlite3
site/
docs/
example/staticfiles/
example/media/
```

!!! tip "A lean context = a fast build"
    The `.dockerignore` keeps `.venv`, the dev SQLite database, the generated site
    and the `docs/` folder out of the image. Less stuff to copy, a faster build and
    a smaller image.

### What's missing for "real" production

!!! danger "This stack is a solid base — harden it before exposing it"
    - **`SECRET_KEY` and passwords** via the orchestrator's *secrets*, never
      hardcoded in the `compose` like here (it's just a demonstration).
    - **HTTPS**: put an Nginx/Traefik or a load balancer in front, terminating TLS.
      Turn on `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`,
      HSTS (see [deploy](deploy.md)).
    - **Backups** of the Postgres volume.
    - **`migrate` as a separate step** when scaling replicas.
    - Run `python manage.py check --deploy` and resolve the warnings.

## Recap

- Docker packages the app into a box; Compose orchestrates app + database with one
  command.
- `Dockerfile`: `uv sync --no-dev --group prod`, copy the lock before the code
  (layer caching).
- `entrypoint.sh` runs `migrate` + `collectstatic` and hands off to Gunicorn.
- `docker-compose.yml`: a `db` service (Postgres with a healthcheck) + `web`
  (`depends_on: healthy`), they find each other by the **service name**; volumes
  for data.
- The `settings` reads the database from the **environment**; WhiteNoise serves
  the static files.
- Before exposing: secrets, HTTPS, backups, a separate `migrate`, `check
  --deploy`.

For the general production checklist (without Docker), see **[deploy](deploy.md)**.
