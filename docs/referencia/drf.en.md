# Reference: DRF — serializers and viewsets

!!! quote "Think like a child 🧒"
    The human browser wants a pretty page (HTML). But a phone app or another
    program wants the data "bare," in **JSON** — just the information, no
    decoration. The **serializer** is the translator that dresses and undresses:
    it turns your Python object into JSON (to send) and the JSON back into an
    object (when receiving), checking that it came in correctly. The **viewset**
    is the waiter of that JSON kitchen.

## Use case

You already have the blog in HTML. Now a mobile app wants to list and create
posts via an API. With DRF, you reuse the **same models** and expose JSON with
very little code:

```python
# apps/blog/api/serializers.py
from rest_framework import serializers

from apps.blog.models import Post


class PostSerializer(serializers.ModelSerializer):
    """Serialize a Post to/from JSON."""

    class Meta:
        model = Post
        fields = ["id", "title", "slug", "body", "status", "published_at"]
        read_only_fields = ["slug", "published_at"]
```

```python
# apps/blog/api/views.py
from rest_framework import viewsets

from apps.blog.models import Post


class PostViewSet(viewsets.ModelViewSet):
    """Full CRUD API for posts."""

    queryset = Post.objects.all()
    serializer_class = PostSerializer
```

A router turns the viewset into all the REST routes. Let's get to the details.

## Possibilities

!!! info "The mirror of the web you already know"
    | Web (HTML) | API (DRF) |
    | --- | --- |
    | `ModelForm` | `ModelSerializer` |
    | Template | Serializer (renders JSON) |
    | `ListView` / `DetailView` | `ViewSet` |
    | `urls.py` + `path` | `Router` |

    Same concepts, different format. If you understood forms and views, you
    understand DRF.

### Types of serializer

| Class | When to use |
| --- | --- |
| `Serializer` | Full control; you declare each field (no model) |
| `ModelSerializer` | Derives the fields from a model (the common one) |
| `HyperlinkedModelSerializer` | Like the above, but relations become URLs |

### The `ModelSerializer`'s `Meta`

| Option | What it does |
| --- | --- |
| `model` | Which model to serialize |
| `fields` | List of fields (or `"__all__"`) |
| `exclude` | Fields to remove (opposite of `fields`) |
| `read_only_fields` | Fields that go out in the JSON but are **not** accepted on write |
| `extra_kwargs` | Per-field tweaks without redeclaring the whole field |
| `depth` | Automatically expands nested relations up to N levels |

```python
class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ["id", "title", "slug", "body", "status", "author"]
        read_only_fields = ["slug"]
        extra_kwargs = {
            "body": {"help_text": "Content in Markdown."},
            "status": {"required": False},
        }
```

!!! danger "`read_only_fields` protects derived fields"
    Fields like `slug`, `published_at`, `created_at` are computed on the server.
    If the client could send them, it would forge data. Mark them `read_only`.
    Same principle as the explicit `fields` in forms: **don't trust the client**.

### Serializer field options

They apply to fields declared manually:

| Option | What it does |
| --- | --- |
| `read_only` | Read-only (goes out in the JSON, doesn't come in) |
| `write_only` | Write-only (comes in, doesn't go out — e.g., password) |
| `required` | Required on input |
| `default` | Default value if absent |
| `allow_null` | Accepts `null` |
| `allow_blank` | Accepts an empty string |
| `source` | Ties the field to another attribute/relation of the object |
| `validators` | List of validators |
| `help_text` | Documentation (shows up in the browsable API) |

### Nested read × write by id (the essential trick)

Think like a child: to **show** the author, you want their full card. To
**choose** the author, you just point your finger ("this one here, number 3").
They are different things:

```python
class PostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)              # (1)!
    tags = TagSerializer(many=True, read_only=True)        # (2)!
    tag_ids = serializers.PrimaryKeyRelatedField(          # (3)!
        many=True, write_only=True,
        queryset=Tag.objects.all(), source="tags",
    )

    class Meta:
        model = Post
        fields = ["id", "title", "author", "tags", "tag_ids"]
```

1. **Read**: the author goes out as a full nested object.
2. **Read**: the tags go out as a list of objects.
3. **Write**: the client sends only `tag_ids: [1, 3]`. `source="tags"` ties this
   write field to the real relation.

### Validation in the serializer

Just like forms, with different names:

```python
class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "author_name", "email", "body"]

    def validate_body(self, value: str) -> str:
        """Validate one field: reject too-short comments."""
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Comment is too short.")
        return value

    def validate(self, attrs: dict) -> dict:
        """Validate across fields."""
        if attrs["author_name"].lower() in attrs["body"].lower():
            raise serializers.ValidationError("Don't repeat your name in the body.")
        return attrs
```

| Web (form) | API (serializer) |
| --- | --- |
| `clean_<field>()` | `validate_<field>(self, value)` |
| `clean()` | `validate(self, attrs)` |

### Types of viewset

| Class | What it delivers |
| --- | --- |
| `ViewSet` | Nothing ready-made; you write each action |
| `GenericViewSet` | Base + mixins that you pick |
| `ReadOnlyModelViewSet` | Only `list` + `retrieve` (read) |
| `ModelViewSet` | Full CRUD: list, retrieve, create, update, destroy |

### Viewset attributes and hooks

| Attribute/method | What it does |
| --- | --- |
| `queryset` | The base of objects |
| `serializer_class` | Which serializer to use |
| `lookup_field` | Field of the detail URL (default `"pk"`; use `"slug"`) |
| `permission_classes` | Who can access |
| `authentication_classes` | How to identify the client |
| `get_queryset()` | Filter the base dynamically (by user, query param) |
| `get_serializer_class()` | Choose the serializer per action |
| `perform_create(serializer)` | Act on create (equivalent to `form_valid`) |
| `perform_update(serializer)` | Act on update |

```python
from django.db.models import QuerySet
from rest_framework import viewsets


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    lookup_field = "slug"

    def get_queryset(self) -> QuerySet[Post]:
        """Anonymous clients see only published posts."""
        base = Post.objects.select_related("author").prefetch_related("tags")
        if self.request.user.is_authenticated:
            return base
        return base.filter(status=Post.Status.PUBLISHED)

    def perform_create(self, serializer: PostSerializer) -> None:
        """Set the author from the logged-in user, never from the payload."""
        serializer.save(author=self.request.user.author_profile)
```

### Extra actions: `@action`

Want an endpoint beyond CRUD (e.g., `/posts/<slug>/publish/`)? Use `@action`:

```python
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request


class PostViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=["post"])
    def publish(self, request: Request, slug: str | None = None) -> Response:
        """POST /api/posts/<slug>/publish/ — publish a single post."""
        post = self.get_object()
        post.status = Post.Status.PUBLISHED
        post.save()
        return Response({"status": "published"})
```

| `@action(...)` | Meaning |
| --- | --- |
| `detail=True` | Acts on **one** object (`/posts/<slug>/publish/`) |
| `detail=False` | Acts on the collection (`/posts/featured/`) |
| `methods=[...]` | Accepted HTTP methods |

### Router: the URLs for free

```python
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("posts", PostViewSet, basename="post")
```

This automatically generates:

| Method + URL | Action |
| --- | --- |
| `GET /posts/` | `list` |
| `POST /posts/` | `create` |
| `GET /posts/<slug>/` | `retrieve` |
| `PUT/PATCH /posts/<slug>/` | `update` |
| `DELETE /posts/<slug>/` | `destroy` |
| `POST /posts/<slug>/publish/` | the `@action` above |

### Ready-made permissions

| Class | Grants access to |
| --- | --- |
| `AllowAny` | Everyone |
| `IsAuthenticated` | Only logged-in users |
| `IsAuthenticatedOrReadOnly` | Everyone reads; only logged-in users write |
| `IsAdminUser` | Only staff |
| `DjangoModelPermissions` | Follows the model's permissions in Django |

## Recap

- The serializer is the Python ↔ JSON translator; the viewset is the API's
  waiter.
- DRF mirrors the web: `ModelSerializer`≈`ModelForm`, `ViewSet`≈CBV,
  `Router`≈urls.
- In `Meta`: explicit `fields`, `read_only_fields` to protect derived ones,
  `extra_kwargs` for fine-tuning.
- Nested read (`author`/`tags`) × write by id (`tag_ids` with `source`).
- Validation: `validate_<field>` (one) and `validate` (several) — mirror of
  `clean`.
- `get_queryset`/`perform_create` are the hooks (like `get_queryset`/`form_valid`).
- `@action` adds extra endpoints; the `Router` generates the REST URLs on its
  own.

You now have the reference for the four layers. Head back to the
[Tutorial](../tutorial/project-setup.md) to see them working together.
