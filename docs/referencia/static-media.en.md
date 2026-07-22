# Reference: static and media files

!!! quote "Think like a child 🧒"
    There are two kinds of thing that aren't "text from the database". The
    **static** files are the toys that come in the game box (the CSS, the
    JavaScript, the logo) — you put them there and they don't change. The
    **media** files are the drawings **the kids make** while playing (profile
    photos, attachments) — they show up later, during use. Django treats the two
    differently.

## Use case

### Static: a CSS file from your app

```text
apps/blog/static/blog/style.css
```

```django
{% load static %}
<link rel="stylesheet" href="{% static 'blog/style.css' %}">
```

### Media: an avatar uploaded by the user

```python
class Profile(models.Model):
    avatar = models.ImageField(upload_to="avatars/%Y/%m/", blank=True)
```

```django
{% if profile.avatar %}
  <img src="{{ profile.avatar.url }}" alt="avatar">
{% endif %}
```

## Possibilities

### Static vs. media: the difference that confuses everyone

| | Static | Media |
| --- | --- | --- |
| What it is | CSS, JS, theme images | User uploads |
| Who creates it | You (dev) | The users (runtime) |
| URL setting | `STATIC_URL` | `MEDIA_URL` |
| Folder setting | `STATIC_ROOT` (collectstatic target) | `MEDIA_ROOT` |
| Command | `collectstatic` | — |
| Model field | — | `FileField` / `ImageField` |

!!! danger "Never point both at the same folder"
    Mixing static and media is asking for trouble: `collectstatic` may overwrite or
    delete uploads. They are separate worlds — separate folders.

### Static: where Django looks

Think like a child: Django has a list of boxes to look through for toys.

| Setting | Role |
| --- | --- |
| `STATIC_URL` | URL prefix (`static/`) |
| `STATICFILES_DIRS` | **Extra** project static folders (outside the apps) |
| `STATIC_ROOT` | Single folder where `collectstatic` **gathers** everything (production) |

```python
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "assets"]     # project statics (optional)
STATIC_ROOT = BASE_DIR / "staticfiles"        # collectstatic target
```

- **`app/static/app/...`** → each app's statics (found automatically).
- **`{% static 'path' %}`** → generates the right URL, never write it by hand.

### `collectstatic`: gather for production

Think like a child: before leaving home, you gather all the scattered toys into a
single backpack (`STATIC_ROOT`), so the delivery person can carry them all at
once.

```bash
python manage.py collectstatic --no-input
```

In development (`DEBUG=True`), `runserver` serves the statics directly — you do
**not** need to run `collectstatic`. It's for production.

### `STORAGES`: how and where to store (modern Django)

The `STORAGES` setting defines the storage backend for `default` (media) and
`staticfiles`:

```python
STORAGES = {
    "default": {                                    # uploads (media)
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {                                # statics
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
```

| Common backend | Stores in |
| --- | --- |
| `FileSystemStorage` | Local disk |
| `whitenoise...CompressedManifestStaticFilesStorage` | Disk, compressed + hash in the name (eternal cache) |
| `storages.backends.s3.S3Storage` (django-storages) | Amazon S3 / compatible |

!!! tip "Hash in the name = safe eternal cache"
    The storage with a *manifest* renames `style.css` to `style.a1b2c3.css`.
    Because the name changes when the content changes, the browser can cache it
    "forever" without serving a stale version. `{% static %}` resolves the hashed
    name on its own.

### Serving media in development

In `DEBUG=True`, add this to the root `urls.py` so `runserver` serves uploads:

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... your routes ...
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

!!! danger "In production, media is NOT served by Django"
    In production, files are served by the web server (Nginx) or a cloud storage
    (S3). Letting Django serve uploads in production is slow and insecure. The
    trick above is **only** for development.

### `FileField` / `ImageField` in practice

| Option | What it does |
| --- | --- |
| `upload_to` | Subfolder inside `MEDIA_ROOT` (accepts `%Y/%m/` or a callable) |
| `storage` | A specific backend for this field |
| `.url` | Public URL of the file |
| `.path` | Path on disk (local storages only) |

```python
def user_directory(instance: "Profile", filename: str) -> str:
    """Store each user's uploads under their own folder."""
    return f"users/{instance.user_id}/{filename}"


class Profile(models.Model):
    avatar = models.ImageField(upload_to=user_directory, blank=True)
```

!!! info "`ImageField` needs Pillow"
    `ImageField` validates that the file is an image — for that, install `Pillow`
    (`uv add pillow`). `FileField` accepts any file, without Pillow.

## Recap

- **Static** (ships with the project) vs. **media** (user upload) — separate
  folders and settings, never mixed.
- Statics: `{% static %}` generates the URL; `STATICFILES_DIRS` (extras),
  `STATIC_ROOT` (`collectstatic` target, production only).
- `STORAGES` defines the backends; a storage with a hash in the name enables an
  eternal cache.
- Media in dev: serve it via `static()` in `urls.py` under `if settings.DEBUG`;
  in production, Nginx/S3.
- `FileField`/`ImageField`: `upload_to` (string or callable), `.url`/`.path`;
  `ImageField` requires Pillow.

Files sorted out. Now let's make the site speak many languages: **[i18n](i18n.md)**.
