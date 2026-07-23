# DRF in depth: auth, throttling, versioning and nested

On the [REST API with DRF](drf.md) page you built the CRUD: serializers,
viewsets and routers. Now we go beyond the basics — the layers that turn a toy
API into a **production** one: who gets in (authentication), what each person
can do (permissions), how often they can knock on the door (throttling), how to
evolve without breaking clients (versioning) and how to return nested data
elegantly (nested serializers).

!!! quote "Think like a child 🧒"
    Picture an **amusement park**. At the entrance, the **turnstile** checks
    your ticket (authentication). Each ride has a **minimum-height sign**
    (permissions: not everyone can hop on). A **staff member counts how many
    times** you've ridden the roller coaster today so you don't hog the queue
    all day (throttling). And when the park refurbishes a ride, it **keeps the
    old one open in a corner** until everyone migrates (versioning). DRF hands
    you a turnstile, signs, a counter and a version map — all ready.

## Use case

The blog got popular. A mobile app consumes the API, and you need:

- **Token login** (mobile doesn't use session cookies).
- **Only the author** can edit their own post.
- **Anonymous** clients knock at most 20 times per minute; **logged-in** ones,
  1000 per day.
- The API has `/api/v1/` and you want to ship `/api/v2/` without breaking v1.
- The post endpoint returns the author, the tags **and** the nested comments.

Let's solve each piece, one at a time.

## Possibilities

### Authentication: who are you?

Authentication **identifies** the client and fills `request.user`. DRF ships
several classes; you pick one or more in `settings.py` (or per view).

| Class | How the client proves identity | When to use |
| --- | --- | --- |
| `SessionAuthentication` | Django session cookie | Front on the same domain, browsable API |
| `BasicAuthentication` | `Authorization: Basic <base64>` | Tests, internal scripts (HTTPS only) |
| `TokenAuthentication` | `Authorization: Token <key>` | Simple apps, one token per user |
| `JWTAuthentication` (simplejwt) | `Authorization: Bearer <jwt>` | Mobile/SPA, tokens with expiry |

#### DRF's classic token

The built-in token is the shortest path: a table storing one key per user.

```python
INSTALLED_APPS = [
    # ...
    "rest_framework",
    "rest_framework.authtoken",
    "apps.blog",
]

REST_FRAMEWORK: dict[str, object] = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
}
```

Run the migration (`python manage.py migrate`) and expose the endpoint that
swaps username/password for a token:

```python
# apps/blog/api/urls.py
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path("auth/token/", obtain_auth_token, name="api-token"),
]
```

```bash
# get the token
curl -X POST http://127.0.0.1:8000/api/auth/token/ \
  -d "username=ada&password=secret123"
# {"token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"}

# use the token
curl http://127.0.0.1:8000/api/posts/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

!!! warning "The classic token never expires"
    The `authtoken` token is permanent until you delete it by hand. For tokens
    with expiry, refresh and rotation, use **JWT** (next). And **always** serve
    the API over HTTPS: a leaked token is full access.

#### JWT with `djangorestframework-simplejwt`

For mobile/SPA, the market standard is JWT: an **access** (short) + **refresh**
(long) pair, with no token table in the database.

```bash
uv add djangorestframework-simplejwt
```

```python
from datetime import timedelta

REST_FRAMEWORK: dict[str, object] = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
}

SIMPLE_JWT: dict[str, object] = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
}
```

```python
# apps/blog/api/urls.py
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("auth/jwt/", TokenObtainPairView.as_view(), name="jwt-obtain"),
    path("auth/jwt/refresh/", TokenRefreshView.as_view(), name="jwt-refresh"),
]
```

```bash
# login → get access + refresh
curl -X POST http://127.0.0.1:8000/api/auth/jwt/ \
  -d "username=ada&password=secret123"
# {"refresh": "eyJ...", "access": "eyJ..."}

# use the access
curl http://127.0.0.1:8000/api/posts/ \
  -H "Authorization: Bearer eyJ..."
```

!!! tip "Short access, long refresh"
    Keep the **access** short (minutes): if it leaks, it doesn't last. The
    **refresh** (days) is stored securely on the client and mints new access
    tokens without asking for the password again. With
    `ROTATE_REFRESH_TOKENS=True`, each refresh issues a new refresh, making
    reuse of a stolen token harder.

### Permissions: what can you do?

Authentication says **who** you are; permission says **what** you can do. DRF
checks a list of classes; if any one denies, the response is `403` (or `401` if
anonymous).

| Class | Effect |
| --- | --- |
| `AllowAny` | Allows everything |
| `IsAuthenticated` | Requires login |
| `IsAuthenticatedOrReadOnly` | Free reads, writes require login |
| `IsAdminUser` | `is_staff` only |
| `DjangoModelPermissions` | Uses the admin's model permissions (`add`/`change`/`delete`) |

When the built-ins aren't enough — "only the **owner** edits" — you write an
object permission:

```python
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.blog.models import Post


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Allow read to anyone, but writes only to the post's author."""

    def has_object_permission(
        self, request: Request, view: APIView, obj: Post
    ) -> bool:
        """Grant safe methods to all, and unsafe ones only to the owner.

        Args:
            request: The incoming request carrying the authenticated user.
            view: The view handling the request.
            obj: The post instance being accessed.

        Returns:
            True if the request is a safe (read-only) method, or if the
            requesting user owns the post's author profile.
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author.user_id == request.user.id
```

```python
from rest_framework import viewsets

from apps.blog.api.permissions import IsAuthorOrReadOnly


class PostViewSet(viewsets.ModelViewSet):
    """Full CRUD API for posts, owner-gated on writes."""

    serializer_class = PostSerializer
    permission_classes = [IsAuthorOrReadOnly]
    lookup_field = "slug"
```

!!! note "`has_permission` vs `has_object_permission`"
    `has_permission` runs **before** fetching the object (applies to list and
    create). `has_object_permission` runs **after**, with the object in hand
    (for detail/update/delete). You need both when you want to gate both general
    access and access to the specific item.

### Throttling: how often?

Throttling **limits the rate** of requests. DRF counts the accesses and returns
`429 Too Many Requests` when the client exceeds the limit.

| Class | Counts per | Typical use |
| --- | --- | --- |
| `AnonRateThrottle` | Anonymous client IP | Curb public scraping/abuse |
| `UserRateThrottle` | Authenticated user | Fair per-account limit |
| `ScopedRateThrottle` | Named "scope" per view | Expensive endpoints (search, upload) |

```python
REST_FRAMEWORK: dict[str, object] = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "20/minute",
        "user": "1000/day",
        "search": "10/minute",
    },
}
```

The rate format is `number/period`, where `period` is `second`, `minute`,
`hour` or `day`. For a dedicated limit on a specific endpoint, use the scope:

```python
from rest_framework.throttling import ScopedRateThrottle
from rest_framework import viewsets


class SearchViewSet(viewsets.ReadOnlyModelViewSet):
    """Expensive full-text search, throttled by its own scope."""

    serializer_class = PostSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "search"
```

!!! warning "Throttle isn't security, it's hygiene"
    DRF throttling keeps counters in the **cache** and serves to contain
    accidental abuse and spikes. It does **not** replace edge rate limiting
    (nginx, WAF, API gateway) against deliberate attacks. Configure a real
    `CACHE` (Redis) — with the per-process local cache, each worker counts
    separately.

### Pagination: slicing lists

You've already seen `PageNumberPagination`. DRF ships three styles; pick with
`DEFAULT_PAGINATION_CLASS` or per view.

| Class | Query params | Good for |
| --- | --- | --- |
| `PageNumberPagination` | `?page=2` | Browsable lists (pages) |
| `LimitOffsetPagination` | `?limit=10&offset=20` | Fine window control |
| `CursorPagination` | `?cursor=cD0y` | Large, high-write feeds (stable, opaque) |

```python
from rest_framework.pagination import CursorPagination


class PostCursorPagination(CursorPagination):
    """Stable, opaque cursor pagination ordered by newest first."""

    page_size = 10
    ordering = "-created_at"


class PostViewSet(viewsets.ModelViewSet):
    """Full CRUD API for posts with cursor pagination."""

    serializer_class = PostSerializer
    pagination_class = PostCursorPagination
```

!!! tip "Cursor for growing feeds"
    In lists where new items arrive all the time, `PageNumberPagination` can
    **repeat or skip** items when something is inserted between two pages.
    `CursorPagination` points to a stable position — ideal for infinite "load
    more".

### Filtering, search and ordering

Filter *backends* read query params and slice the queryset before serializing.
Search and ordering come with DRF itself; per-field filters need the
[`django-filter`](../libs/django-filter.md) library.

```bash
uv add django-filter
```

```python
REST_FRAMEWORK: dict[str, object] = {
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
}
```

```python
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets


class PostViewSet(viewsets.ModelViewSet):
    """Full CRUD API for posts with filtering, search and ordering."""

    serializer_class = PostSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "author"]
    search_fields = ["title", "body"]
    ordering_fields = ["published_at", "created_at"]
    ordering = ["-created_at"]
```

This enables, for free:

```bash
# exact per-field filter (django-filter)
curl "http://127.0.0.1:8000/api/posts/?status=published&author=3"

# text search (SearchFilter)
curl "http://127.0.0.1:8000/api/posts/?search=django"

# ordering (OrderingFilter)
curl "http://127.0.0.1:8000/api/posts/?ordering=-published_at"
```

!!! info "`SearchFilter` prefixes"
    In `search_fields` you can prefix the field: `^` (starts with), `=` (exact
    match), `@` (full-text search on PostgreSQL) and `$` (regex). With no
    prefix, it's `icontains` (contains, case-insensitive).

### Versioning: evolve without breaking

Versioning makes `request.version` available so you can change behavior without
breaking old clients. Pick **one** scheme.

| Scheme | Where the version lives | Example |
| --- | --- | --- |
| `URLPathVersioning` | In the URL path | `/api/v1/posts/` |
| `NamespaceVersioning` | In the URL namespace | `include(..., namespace="v1")` |
| `AcceptHeaderVersioning` | In the `Accept` header | `Accept: application/json; version=1.0` |
| `QueryParameterVersioning` | In a query param | `/api/posts/?version=1.0` |
| `HostNameVersioning` | In the subdomain | `v1.api.example.com` |

The most common and explicit one is `URLPathVersioning`:

```python
REST_FRAMEWORK: dict[str, object] = {
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_VERSION": "v1",
    "ALLOWED_VERSIONS": ["v1", "v2"],
}
```

```python
# config/urls.py
from django.urls import include, path

urlpatterns = [
    path("api/<version>/", include("apps.blog.api.urls")),
]
```

Inside the view, `request.version` tells which version the client asked for:

```python
from rest_framework import viewsets


class PostViewSet(viewsets.ModelViewSet):
    """Full CRUD API for posts, serializer chosen per API version."""

    lookup_field = "slug"

    def get_serializer_class(self) -> type[PostSerializer]:
        """Return the serializer matching the requested API version.

        Returns:
            PostSerializerV2 when the client asked for v2, otherwise the
            v1 serializer.
        """
        if self.request.version == "v2":
            return PostSerializerV2
        return PostSerializer
```

!!! tip "Pick a scheme and match the route"
    The versioning scheme must match the URL design: `URLPathVersioning`
    requires the `<version>` in the `path`. Pin `ALLOWED_VERSIONS` so DRF
    rejects (`404`) nonexistent versions instead of silently serving the
    default.

### Nested serializers and `drf-nested-routers`

Nesting objects on read is common: the post carries author, tags and comments.

```python
from rest_framework import serializers

from apps.blog.models import Author, Comment, Post, Tag


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "display_name"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "author_name", "body", "created_at"]


class PostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id", "title", "slug", "author", "body",
            "tags", "comments", "comment_count", "status",
            "published_at", "created_at",
        ]

    def get_comment_count(self, obj: Post) -> int:
        """Return how many comments the post has.

        Args:
            obj: The post instance being serialized.

        Returns:
            The number of related comments.
        """
        return obj.comments.count()
```

`SerializerMethodField` is a **read-only computed field**: DRF calls
`get_<name>(self, obj)` and uses the return value. Perfect for aggregates and
derivations that don't exist as a column.

!!! warning "N+1 lives in the nested fields"
    Each nested relation and each `SerializerMethodField` that queries the
    database can fire one query per object. Solve it in `get_queryset` with
    `select_related` (FK) and `prefetch_related` (M2M/reverse), and prefer an
    annotated `Count(...)` over `.count()` per item when the list is large.

For **truly nested URLs** — `/api/posts/<slug>/comments/` — the default router
isn't enough. Use `drf-nested-routers`:

```bash
uv add drf-nested-routers
```

```python
# apps/blog/api/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from apps.blog.api.views import CommentViewSet, PostViewSet

router = DefaultRouter()
router.register("posts", PostViewSet, basename="post")

posts_router = NestedDefaultRouter(router, "posts", lookup="post")
posts_router.register("comments", CommentViewSet, basename="post-comments")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(posts_router.urls)),
]
```

```python
from django.db.models import QuerySet
from rest_framework import viewsets

from apps.blog.models import Comment


class CommentViewSet(viewsets.ModelViewSet):
    """Comments scoped to a single parent post from the nested URL."""

    serializer_class = CommentSerializer

    def get_queryset(self) -> QuerySet[Comment]:
        """Return only the comments belonging to the URL's parent post.

        Returns:
            Comments filtered by the ``post_slug`` captured from the
            nested route.
        """
        return Comment.objects.filter(post__slug=self.kwargs["post_slug"])
```

This generates `GET /api/posts/<slug>/comments/` and friends, with `post_slug`
arriving in `self.kwargs`.

### Validation in the serializer

The serializer validates like a `ModelForm`. There are three levels:

```python
from rest_framework import serializers

from apps.blog.models import Post


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ["id", "title", "slug", "body", "status", "published_at"]

    def validate_title(self, value: str) -> str:
        """Reject titles that are too short.

        Args:
            value: The submitted title.

        Returns:
            The validated title.

        Raises:
            serializers.ValidationError: If the title has fewer than 5 chars.
        """
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Title must have at least 5 characters.")
        return value

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        """Ensure published posts carry a publication date.

        Args:
            attrs: The partially validated field values.

        Returns:
            The validated attribute mapping.

        Raises:
            serializers.ValidationError: If a published post lacks a date.
        """
        if attrs.get("status") == Post.Status.PUBLISHED and not attrs.get("published_at"):
            raise serializers.ValidationError(
                {"published_at": "A published post must have a publication date."}
            )
        return attrs
```

- **`validate_<field>`** — validates a single field.
- **`validate`** — validates the whole (rules that cross fields).
- **Field validators** — like `UniqueValidator`, declared on the field.

### OpenAPI/Swagger with `drf-spectacular`

A production API needs browsable documentation. `drf-spectacular` generates an
**OpenAPI 3** schema from your serializers and views.

```bash
uv add drf-spectacular
```

```python
INSTALLED_APPS = [
    # ...
    "rest_framework",
    "drf_spectacular",
]

REST_FRAMEWORK: dict[str, object] = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS: dict[str, object] = {
    "TITLE": "Blog API",
    "DESCRIPTION": "REST API for the Django Survival Guide blog.",
    "VERSION": "1.0.0",
}
```

```python
# config/urls.py
from django.urls import path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
```

Open **<http://127.0.0.1:8000/api/docs/>** for the interactive Swagger UI, or
consume the raw schema at `/api/schema/`.

!!! note "Annotate where the schema can't guess"
    `drf-spectacular` infers almost everything from serializers, but for dynamic
    fields or custom views use the `@extend_schema` decorator to describe
    parameters and responses. A correct schema is gold for auto-generated
    clients. See more libraries in [Related libraries](../libs/afins.md).

```mermaid
flowchart LR
    C["Client"] --> A["Authentication<br/>(who?)"]
    A --> P["Permission<br/>(may they?)"]
    P --> T["Throttle<br/>(how often?)"]
    T --> V["View / ViewSet"]
    V --> S["Serializer<br/>(validate + JSON)"]
    S --> C
```

!!! quote "📖 In the official docs"
    - [Authentication](https://www.django-rest-framework.org/api-guide/authentication/)
    - [Throttling](https://www.django-rest-framework.org/api-guide/throttling/)
    - [Versioning](https://www.django-rest-framework.org/api-guide/versioning/)

## Recap

- **Authentication** identifies the client: `Session` for a front on the same
  domain, `Token` for simple cases, **JWT (simplejwt)** for mobile/SPA with
  expiry.
- **Permissions** decide what each one can do; write `has_object_permission`
  for owner rules.
- **Throttling** (`Anon`/`User`/`Scoped`) contains abuse via cache — it's not a
  replacement for edge rate limiting.
- **Pagination** has three styles; `CursorPagination` shines in large feeds.
- **Filtering/search/ordering** come from the backends (`DjangoFilterBackend`,
  `SearchFilter`, `OrderingFilter`).
- **Versioning**: pick a scheme (`URLPathVersioning` is the most explicit) and
  use `request.version` to branch behavior.
- **Nested serializers** + `SerializerMethodField` for rich reads;
  `drf-nested-routers` for truly nested URLs. Watch out for N+1.
- **Validation** at three levels: `validate_<field>`, `validate` and validators.
- **`drf-spectacular`** generates OpenAPI 3 and a browsable Swagger UI.

With auth, limits, versions and docs in place, your API is ready for the world.
Come back to the [DRF basics](drf.md) whenever you need, and explore the
ecosystem in [Related libraries](../libs/afins.md).
