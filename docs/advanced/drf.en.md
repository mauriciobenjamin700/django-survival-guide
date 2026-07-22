# REST API with DRF

So far, the blog renders **HTML** on the server. Now we're going to expose the **same
models** as a **REST API** in JSON, using the
[Django REST Framework](https://www.django-rest-framework.org/) (DRF).

!!! quote "The mental bridge"
    DRF is the mirror of the web part you already know:

    | Web (HTML) | API (DRF) |
    | --- | --- |
    | `ModelForm` | `ModelSerializer` |
    | Template | Serializer (renders JSON) |
    | `ListView`/`DetailView` | `ViewSet` |
    | `urls.py` + `path` | `Router` |

    Same object orientation, same philosophy — only the output format changes.

## Installation and configuration

```bash
uv add djangorestframework
```

Register it in `INSTALLED_APPS` and configure the default behavior:

```python
INSTALLED_APPS = [
    # ...
    "rest_framework",
    "apps.blog",
]

REST_FRAMEWORK: dict[str, object] = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 5,
}
```

!!! info "`IsAuthenticatedOrReadOnly`"
    This default permission allows **reading** (GET) for anyone, but requires
    **login** to write (POST/PUT/DELETE). It's the typical behavior of a
    blog: everyone reads, only authors publish.

## Serializers: validation and JSON

A `ModelSerializer` derives the fields from the model, validates the input, and serializes the
output — exactly like a `ModelForm`, but for JSON:

```python
from rest_framework import serializers

from apps.blog.models import Author, Post, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class PostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)                 # (1)!
    tags = TagSerializer(many=True, read_only=True)           # (2)!
    tag_ids = serializers.PrimaryKeyRelatedField(             # (3)!
        many=True, write_only=True, queryset=Tag.objects.all(),
        source="tags", required=False,
    )

    class Meta:
        model = Post
        fields = [
            "id", "title", "slug", "author", "body",
            "tags", "tag_ids", "status", "published_at", "created_at",
        ]
        read_only_fields = ["slug", "published_at", "created_at"]
```

1. **Read**: the author comes out as a nested object (`{"id":.., "display_name":..}`).
2. **Read**: the tags come out as a list of objects.
3. **Write**: the client sends `tag_ids: [1, 2]` (just the IDs). `source="tags"`
   links this write field to the real relation.

!!! tip "Separate reading from writing"
    Nesting objects is great for *reading* (the client receives everything spelled out), but
    bad for *writing* (the client would have to resend the whole object). The
    `tags` (read-only nested) + `tag_ids` (write-only by PK) pair solves both
    sides clearly. `read_only_fields` protects derived fields, as we did
    in the forms.

## ViewSets: CRUD in one class

A `ViewSet` is the API version of the generic views: one class delivers list,
retrieve, create, update, and destroy all at once.

```python
from django.db.models import QuerySet
from rest_framework import viewsets

from apps.blog.models import Post


class PostViewSet(viewsets.ModelViewSet):
    """Full CRUD API for posts."""

    serializer_class = PostSerializer
    lookup_field = "slug"

    def get_queryset(self) -> QuerySet[Post]:
        """Return posts visible to the current client."""
        base = Post.objects.select_related("author").prefetch_related("tags")
        if self.request.user.is_authenticated:
            return base
        return base.filter(status=Post.Status.PUBLISHED)

    def perform_create(self, serializer: PostSerializer) -> None:
        """Attach the logged-in user's author profile to the new post."""
        serializer.save(author=self.request.user.author_profile)
```

Notice how the tutorial's concepts repeat:

- **`get_queryset()`** — same idea as `ListView`: anonymous users only see published;
  logged-in users see everything. And we resolve the N+1 with `select_related`/`prefetch_related`.
- **`perform_create()`** — the equivalent of `form_valid`: it injects the author from
  the logged-in user, never from the payload.
- **`lookup_field = "slug"`** — the detail URL uses the slug, not the id.

## Routers: automatic URLs

A `DefaultRouter` inspects each ViewSet and **generates all the REST routes**:

```python
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.blog.api.views import CommentViewSet, PostViewSet, TagViewSet

app_name = "blog-api"

router = DefaultRouter()
router.register("posts", PostViewSet, basename="post")
router.register("tags", TagViewSet, basename="tag")
router.register("comments", CommentViewSet, basename="comment")

urlpatterns = [path("", include(router.urls))]
```

Mounted at `/api/` in the root `urls.py`, this generates:

| Method + URL | Action |
| --- | --- |
| `GET /api/posts/` | list (paginated) |
| `POST /api/posts/` | create (requires login) |
| `GET /api/posts/<slug>/` | detail |
| `PUT/PATCH /api/posts/<slug>/` | update |
| `DELETE /api/posts/<slug>/` | delete |

## Trying it out

Bring the server up and open **<http://127.0.0.1:8000/api/>** — DRF brings a **browsable
API** right in the browser, great for exploring.

Via the command line:

```bash
# listar (público)
curl http://127.0.0.1:8000/api/posts/

# um post
curl http://127.0.0.1:8000/api/posts/why-class-based-views-scale/
```

The paginated response has the format:

```json
{
  "count": 4,
  "next": null,
  "previous": null,
  "results": [ { "id": 1, "title": "...", "author": {...}, "tags": [...] } ]
}
```

## Recap

- DRF exposes the same models as JSON, mirroring the web concepts.
- **Serializer** = the API's `ModelForm`: validates and serializes; protect derived
  fields with `read_only_fields`.
- Separate nested reading from writing by PK (`tags` + `tag_ids`).
- **ViewSet** = the API's CBV; `get_queryset`/`perform_create` repeat what you already
  did. Watch the N+1 here too.
- **Router** generates the REST routes automatically and a browsable API.

We built web and API on the same base. What's left is making sure everything keeps
working as the project grows — the **[Tests](testing.md)**.
