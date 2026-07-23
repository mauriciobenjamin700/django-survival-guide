# Reference: storages (file storage)

!!! quote "Think like a child 🧒"
    When someone uploads a photo, it has to live somewhere. A **storage** is the
    "cabinet" where files sit. It can be a drawer on your computer (local disk) or a
    giant warehouse in the cloud (S3). Django's trick: your code talks to an
    **abstract** cabinet — swapping cabinets doesn't change the code.

## Use case

In development uploads sit on disk; in production, on Amazon S3. You don't change
the model — just the configured **storage**:

```python
# the model is always the same
class Profile(models.Model):
    avatar = models.ImageField(upload_to="avatars/")
```

```python
# settings.py — dev: local disk
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# settings.py — production: S3 (via django-storages)
STORAGES = {
    "default": {"BACKEND": "storages.backends.s3.S3Storage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
```

`profile.avatar.url` works the same in both — only where it points changes.

## What's possible

### The `STORAGES` setting

Think like a child: two cabinets with fixed nicknames.

| Nickname | Stores |
| --- | --- |
| `default` | User uploads (what `FileField`/`ImageField` write) |
| `staticfiles` | Static files (CSS/JS), the destination of `collectstatic` |

```python
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": "/data/media", "base_url": "/media/"},
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
```

### Common backends

| Backend | Cabinet |
| --- | --- |
| `FileSystemStorage` | Local disk |
| `whitenoise...CompressedManifestStaticFilesStorage` | Disk, compressed + hashed name |
| `storages.backends.s3.S3Storage` | Amazon S3 / compatible (MinIO, R2) |
| `storages.backends.gcloud.GoogleCloudStorage` | Google Cloud Storage |
| `storages.backends.azure_storage.AzureStorage` | Azure Blob |

The cloud ones come from the [django-storages](https://django-storages.readthedocs.io/) package:

```bash
uv add "django-storages[s3]"
```

### A storage's API

Every storage — local or cloud — exposes the same interface. That's why swapping
the backend doesn't break your code:

| Method/attribute | Does |
| --- | --- |
| `storage.save(name, content)` | Writes a file, returns the final name |
| `storage.open(name)` | Opens for reading |
| `storage.delete(name)` | Deletes |
| `storage.exists(name)` | Exists? |
| `storage.url(name)` | Public URL |
| `storage.size(name)` | Size in bytes |

```python
from django.core.files.base import ContentFile
from django.core.files.storage import storages

default = storages["default"]
name = default.save("reports/x.txt", ContentFile(b"content"))
url = default.url(name)
```

### `upload_to`: where inside the cabinet

```python
def by_user(instance, filename: str) -> str:
    """Store each user's uploads under their own folder."""
    return f"users/{instance.user_id}/{filename}"


class Profile(models.Model):
    avatar = models.ImageField(upload_to=by_user)     # or upload_to="avatars/%Y/%m/"
```

- **String** with `strftime` (`"avatars/%Y/%m/"`) → subfolder by date.
- **Callable** `(instance, filename) -> str` → full control of the path.

### Per-field storage

A field can use a different cabinet from the `default`:

```python
from storages.backends.s3 import S3Storage

private_store = S3Storage(bucket_name="private", default_acl="private")


class Invoice(models.Model):
    pdf = models.FileField(storage=private_store)
```

!!! tip "Private files: serve them via a signed URL"
    Sensitive uploads (invoices, documents) shouldn't be public. On cloud storages,
    use a private ACL and generate **signed URLs** (temporary ones) for the
    download — `django-storages` does this via `querystring_auth`.

### Best practices

!!! danger "In production, Django does NOT serve the files"
    In production, uploads are served by the cloud storage (S3) or by the web server
    (Nginx) — never by the Django process, which is slow and insecure for that. The
    trick of serving media through `runserver` (see [static-media](static-media.md))
    is for development only.

!!! tip "Never trust the uploaded file's name"
    The storage already sanitizes it and, if there's a collision, appends a random
    suffix. Don't use the raw upload name in paths without going through
    `upload_to`.

!!! quote "📖 In the official docs"
    - [File storage API](https://docs.djangoproject.com/en/stable/ref/files/storage/)
    - [django-storages](https://django-storages.readthedocs.io/)

## Recap

- A storage is the "cabinet" of files; the code talks to an **abstract**
  interface, so swapping disk↔cloud doesn't change the models.
- `STORAGES` defines `default` (uploads) and `staticfiles`; backends: local,
  WhiteNoise, S3/GCS/Azure (via django-storages).
- Common API: `save`/`open`/`delete`/`url`/`exists`. `upload_to` (string with date
  or callable) decides the path; `storage=` swaps the cabinet per field.
- Private files → private ACL + signed URL. In production, the cloud/Nginx serves
  them, not Django.

You've walked through the Django reference from end to end. 🎉 Go back to the
[reference map](index.md) or to the [tutorial](../tutorial/project-setup.md).
