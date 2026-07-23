# Friends: the essential catalog

Beyond the big ones (allauth, Celery, Channels), there's a handful of libraries that
show up in almost every serious Django project. Here's the catalog with the **what for**
and the minimum to get started.

!!! quote "Think like a child 🧒"
    These are the **tools in the toolbox**: the flashlight that shows what's stuck
    (debug), the key that organizes secrets (environ), the megaphone that documents the
    API. You don't use them all the time, but it's good to know they exist when you need them.

## Development

### django-debug-toolbar — the flashlight

Shows, on each page, the **SQL queries**, the timing, the templates, the cache. It's the
#1 way to hunt down the [N+1](../referencia/querysets-api.md).

```bash
uv add django-debug-toolbar
```
```python
INSTALLED_APPS = ["debug_toolbar", ...]
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware", ...]
INTERNAL_IPS = ["127.0.0.1"]
# urls.py: path("__debug__/", include("debug_toolbar.urls"))
```

!!! danger "Development only"
    The toolbar exposes internal data. Enable it **only** with `DEBUG=True`; never
    leave it in a public environment.

### django-extensions — the Swiss army knife

`shell_plus` (a shell with all models already imported), `runserver_plus`,
`graph_models` (an ORM diagram), `show_urls`.

```bash
uv add django-extensions
# INSTALLED_APPS += ["django_extensions"]
python manage.py shell_plus
```

## Configuration

### django-environ — the key to the secrets

Reads `.env` and converts types, keeping [settings](../referencia/settings.md) clean.

```bash
uv add django-environ
```
```python
import environ
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DEBUG")
DATABASES = {"default": env.db("DATABASE_URL")}   # parses postgres://... on its own
```

## API (DRF)

### djangorestframework-simplejwt — token login

For APIs consumed by a mobile/SPA app, the flow is **JWT**, not session/cookie.

```bash
uv add djangorestframework-simplejwt
```
```python
# urls.py
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
path("api/token/", TokenObtainPairView.as_view()),
path("api/token/refresh/", TokenRefreshView.as_view()),
```
The client sends `Authorization: Bearer <token>` on its requests.

### drf-spectacular — OpenAPI documentation

Generates an **OpenAPI 3** schema and a browsable UI (Swagger/Redoc) for your API,
by reading the serializers/viewsets.

```bash
uv add drf-spectacular
```
```python
REST_FRAMEWORK = {"DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema"}
# urls.py: SpectacularAPIView (schema) + SpectacularSwaggerView (UI)
```

### django-cors-headers — unblock the separate frontend

If the frontend (React/Vite) runs on a **different origin** (`localhost:5173`) and calls your
API, the browser blocks it because of CORS. This lib unblocks the right origins.

```bash
uv add django-cors-headers
```
```python
INSTALLED_APPS = ["corsheaders", ...]
MIDDLEWARE = ["corsheaders.middleware.CorsMiddleware", ...]  # right at the top
CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]
```

!!! warning "CORS isn't security — it's a browser permission"
    Never use `CORS_ALLOW_ALL_ORIGINS = True` in production. List the exact
    origins. And remember: CORS controls the **browser**, it doesn't replace authentication.

## Files and images

### Pillow — images

Required for the `ImageField` and to resize/validate images.

```bash
uv add pillow
```

### django-storages + WhiteNoise

Cloud storage (S3) and static files in production — covered in
**[Storages](../referencia/storages.md)** and **[static-media](../referencia/static-media.md)**.

## Summary table

| Library | Category | What for |
| --- | --- | --- |
| django-debug-toolbar | Dev | See SQL/timing/queries (hunt N+1) |
| django-extensions | Dev | `shell_plus`, diagrams, utilities |
| django-environ | Config | Read a typed `.env` |
| djangorestframework-simplejwt | API | JWT authentication |
| drf-spectacular | API | OpenAPI/Swagger documentation |
| django-cors-headers | API | Unblock a frontend on another origin |
| Pillow | Files | Images (`ImageField`) |
| django-storages | Files | Cloud uploads (S3/GCS/Azure) |

!!! tip "Don't install everything at once"
    Add a lib when the problem shows up, not "just in case". Every
    dependency is maintenance. The **dev** ones (toolbar, extensions) go only in the
    development group (`uv add --group dev ...`).

## Recap

- **Dev**: debug-toolbar (SQL/queries, only under `DEBUG`), extensions (`shell_plus`).
- **Config**: django-environ (typed `.env`).
- **API**: simplejwt (JWT), drf-spectacular (OpenAPI), cors-headers (separate
  frontend — CORS isn't security).
- **Files**: Pillow (images), django-storages (cloud).
- Install on demand; dev libs in the `dev` group.

Back to infrastructure: how to bring all of this up in containers —
**[containerized services](containers.md)**.
