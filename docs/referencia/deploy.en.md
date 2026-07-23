# Reference: deploy

!!! quote "Think like a child 🧒"
    So far you've played inside the house (`runserver`, just for you). **Deploy** is
    taking the toy to the playground, where anyone can use it. Out there the rules
    are different: the door has to be locked (`DEBUG=False`), a real grown-up looks
    after the gate (Gunicorn, not `runserver`), and the fixed toys (CSS, images) go
    into a tidy box (static files).

## Use case

You want to get the blog live safely. The path: adjust settings via the
environment, collect the static files, and serve with a production server:

```bash
# 1. Check whether it's production-ready
DJANGO_DEBUG=false python manage.py check --deploy

# 2. Gather the static files into one place
python manage.py collectstatic --no-input

# 3. Apply migrations
python manage.py migrate

# 4. Serve with Gunicorn (not with runserver!)
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

## Possibilities

### `runserver` is for development only

!!! danger "Never use `runserver` in production"
    It's single-threaded, unoptimized, and Django itself warns it's not meant for
    that. In production, a **WSGI/ASGI server** handles the requests: Gunicorn or
    Uvicorn.

| Type | Server | Points to |
| --- | --- | --- |
| WSGI (synchronous) | Gunicorn | `config.wsgi:application` |
| ASGI (asynchronous) | Uvicorn / Gunicorn+Uvicorn workers | `config.asgi:application` |

```bash
# WSGI
gunicorn config.wsgi:application --workers 3 --bind 0.0.0.0:8000

# ASGI
uvicorn config.asgi:application --host 0.0.0.0 --port 8000
```

### The settings security checklist

Run `python manage.py check --deploy` and resolve the warnings. The main ones:

```python
DEBUG = False                                   # never True in production
ALLOWED_HOSTS = ["myblog.com", "www.myblog.com"]
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]    # from the environment, never in Git

SECURE_SSL_REDIRECT = True                       # forces HTTPS
SESSION_COOKIE_SECURE = True                     # cookie only over HTTPS
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000                   # HSTS (1 year)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

!!! danger "The deadly trio: `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`"
    - `DEBUG=True` in production **leaks** stack traces with sensitive data.
    - `SECRET_KEY` in Git = anyone can forge sessions and tokens.
    - An empty/`*` `ALLOWED_HOSTS` opens you up to Host header attacks.

    Think like a child: these are the three locks on the door. Going out without
    them is leaving the house wide open.

### Static files

Think like a child: the statics (CSS, JS, theme images) are the toys that
**don't change**. In production you gather them all into a box (`STATIC_ROOT`) and
someone efficient hands them out.

```python
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"     # where collectstatic gathers everything

# MEDIA = files UPLOADED by users (uploads) — kept separate from statics
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
```

```bash
python manage.py collectstatic --no-input
```

!!! info "Static vs. media"
    - **Static**: ships with the project (CSS, JS). You control it. `collectstatic`.
    - **Media**: uploaded by users (avatars, attachments). Changes at runtime.

    Never mix the two directories.

#### WhiteNoise: serving statics without Nginx

For simple deploys (Heroku, a single container), **WhiteNoise** lets Django itself
serve the statics efficiently:

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",   # right after Security
    # ...
]
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
```

### Environment variables

Everything that changes between environments comes from the environment, not from
the code:

| Variable | Example |
| --- | --- |
| `DJANGO_SECRET_KEY` | (a long, random key) |
| `DJANGO_DEBUG` | `false` |
| `DJANGO_ALLOWED_HOSTS` | `myblog.com,www.myblog.com` |
| `DATABASE_URL` | `postgres://user:pass@host:5432/db` |

### A minimal `Dockerfile`

```dockerfile
FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --no-dev --frozen

COPY . .
RUN uv run python manage.py collectstatic --no-input

CMD ["uv", "run", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### The right order at deploy time

```mermaid
flowchart LR
    A[New code] --> B[migrate]
    B --> C[collectstatic]
    C --> D[Restart Gunicorn]
    D --> E[Health check]
```

!!! tip "Migrate before switching to the code that already uses the new schema"
    Run `migrate` **before** bringing up the process that expects the new tables.
    If the new app comes up before the migration, it breaks when it accesses
    columns that don't exist yet.

!!! quote "📖 In the official docs"
    - [Deployment](https://docs.djangoproject.com/en/stable/howto/deployment/)
    - [Deployment checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)

## Recap

- `runserver` **never** in production — use Gunicorn (WSGI) or Uvicorn (ASGI).
- Lock down security: `DEBUG=False`, `SECRET_KEY` from the environment,
  restricted `ALLOWED_HOSTS`, `Secure` cookies, HSTS. Validate with `check --deploy`.
- Statics: `collectstatic` gathers into `STATIC_ROOT`; **WhiteNoise** serves them in
  simple deploys. Media (uploads) stays separate.
- Sensitive configuration comes from **environment variables**.
- Order: `migrate` → `collectstatic` → restart the server → health check.

You now have the Django reference from model to deploy. Come back to the
[Tutorial](../tutorial/project-setup.md) whenever you want to see it all together. 🎉
