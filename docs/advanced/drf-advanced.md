# DRF a fundo: auth, throttling, versioning e nested

Na página [API REST com DRF](drf.md) você montou o CRUD: serializers, viewsets e
routers. Agora vamos além do básico — as camadas que transformam uma API de
brinquedo numa API **de produção**: quem pode entrar (autenticação), o que cada
um pode fazer (permissões), quantas vezes pode bater na porta (throttling), como
evoluir sem quebrar clientes (versioning) e como devolver dados aninhados de
forma elegante (nested serializers).

!!! quote "Pensa como criança 🧒"
    Pensa num **parque de diversões**. Na entrada, a **catraca** confere seu
    ingresso (autenticação). Cada brinquedo tem uma **placa de altura mínima**
    (permissões: nem todo mundo pode subir). O **funcionário conta quantas vezes**
    você já andou na montanha-russa hoje pra não deixar furar a fila o dia todo
    (throttling). E quando o parque reforma um brinquedo, ele **mantém o antigo
    aberto num canto** até todo mundo migrar (versioning). DRF te dá uma catraca,
    placas, um contador e um mapa de versões — tudo pronto.

## Caso de uso

O blog virou popular. Um app mobile consome a API, e você precisa:

- **Login por token** (o mobile não usa cookies de sessão).
- **Só o autor** pode editar o próprio post.
- **Anônimos** batem no máximo 20 vezes por minuto; **logados**, 1000 por dia.
- A API tem `/api/v1/` e você quer poder lançar `/api/v2/` sem quebrar o v1.
- O endpoint de post traz o autor, as tags **e** os comentários aninhados.

Vamos resolver cada pedaço, um de cada vez.

## Possibilidades

### Autenticação: quem é você?

A autenticação **identifica** o cliente e preenche `request.user`. DRF traz
várias classes; você escolhe uma ou mais no `settings.py` (ou por view).

| Classe | Como o cliente prova quem é | Quando usar |
| --- | --- | --- |
| `SessionAuthentication` | Cookie de sessão do Django | Front no mesmo domínio, API navegável |
| `BasicAuthentication` | `Authorization: Basic <base64>` | Testes, scripts internos (só com HTTPS) |
| `TokenAuthentication` | `Authorization: Token <chave>` | Apps simples, um token por usuário |
| `JWTAuthentication` (simplejwt) | `Authorization: Bearer <jwt>` | Mobile/SPA, tokens com expiração |

#### Token clássico do DRF

O token embutido é o caminho mais curto: uma tabela que guarda uma chave por
usuário.

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

Rode a migration (`python manage.py migrate`) e exponha o endpoint que troca
usuário/senha por um token:

```python
# apps/blog/api/urls.py
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path("auth/token/", obtain_auth_token, name="api-token"),
]
```

```bash
# pega o token
curl -X POST http://127.0.0.1:8000/api/auth/token/ \
  -d "username=ada&password=segredo123"
# {"token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"}

# usa o token
curl http://127.0.0.1:8000/api/posts/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

!!! warning "Token clássico não expira"
    O token do `authtoken` é permanente até você apagá-lo à mão. Para tokens com
    validade, refresh e rotação, use **JWT** (a seguir). E **sempre** sirva a API
    por HTTPS: um token vazado é acesso total.

#### JWT com `djangorestframework-simplejwt`

Para mobile/SPA, o padrão de mercado é JWT: um par **access** (curto) +
**refresh** (longo), sem tabela de tokens no banco.

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
# login → recebe access + refresh
curl -X POST http://127.0.0.1:8000/api/auth/jwt/ \
  -d "username=ada&password=segredo123"
# {"refresh": "eyJ...", "access": "eyJ..."}

# usa o access
curl http://127.0.0.1:8000/api/posts/ \
  -H "Authorization: Bearer eyJ..."
```

!!! tip "Access curto, refresh longo"
    Deixe o **access** curto (minutos): se vazar, dura pouco. O **refresh**
    (dias) fica guardado com segurança no cliente e gera novos access sem
    pedir senha de novo. Com `ROTATE_REFRESH_TOKENS=True`, cada refresh emite um
    novo refresh, dificultando reuso de um token roubado.

### Permissões: o que você pode fazer?

Autenticação diz **quem** é; permissão diz **o que** pode. DRF checa uma lista de
classes; se qualquer uma negar, a resposta é `403` (ou `401` se anônimo).

| Classe | Efeito |
| --- | --- |
| `AllowAny` | Libera tudo |
| `IsAuthenticated` | Exige login |
| `IsAuthenticatedOrReadOnly` | Leitura livre, escrita exige login |
| `IsAdminUser` | Só `is_staff` |
| `DjangoModelPermissions` | Usa as permissões de model do admin (`add`/`change`/`delete`) |

Quando as embutidas não bastam — "só o **dono** edita" — você escreve uma
permissão de objeto:

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
    `has_permission` roda **antes** de buscar o objeto (vale para a lista e o
    create). `has_object_permission` roda **depois**, com o objeto em mãos (para
    detalhe/update/delete). Precisa das duas quando quer barrar tanto o acesso
    geral quanto o acesso ao item específico.

### Throttling: com que frequência?

Throttling **limita a taxa** de requisições. DRF conta os acessos e devolve
`429 Too Many Requests` quando o cliente estoura o limite.

| Classe | Conta por | Uso típico |
| --- | --- | --- |
| `AnonRateThrottle` | IP do cliente anônimo | Frear scraping/abuso público |
| `UserRateThrottle` | Usuário autenticado | Limite justo por conta |
| `ScopedRateThrottle` | "Escopo" nomeado por view | Endpoints caros (busca, upload) |

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

O formato da taxa é `numero/periodo`, onde `periodo` é `second`, `minute`,
`hour` ou `day`. Para um limite dedicado num endpoint específico, use o escopo:

```python
from rest_framework.throttling import ScopedRateThrottle
from rest_framework import viewsets


class SearchViewSet(viewsets.ReadOnlyModelViewSet):
    """Expensive full-text search, throttled by its own scope."""

    serializer_class = PostSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "search"
```

!!! warning "Throttle não é segurança, é higiene"
    O throttling do DRF guarda contadores no **cache** e serve para conter abuso
    acidental e picos. Ele **não** substitui rate limiting de borda (nginx,
    WAF, API gateway) contra ataques deliberados. Configure um `CACHE` de verdade
    (Redis) — com o cache local por processo, cada worker conta separado.

### Paginação: fatiando listas

Você já viu `PageNumberPagination`. DRF traz três estilos; escolha por
`DEFAULT_PAGINATION_CLASS` ou por view.

| Classe | Query params | Bom para |
| --- | --- | --- |
| `PageNumberPagination` | `?page=2` | Listas navegáveis (páginas) |
| `LimitOffsetPagination` | `?limit=10&offset=20` | Controle fino de janela |
| `CursorPagination` | `?cursor=cD0y` | Feeds grandes, alta escrita (estável, opaco) |

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

!!! tip "Cursor para feeds que crescem"
    Em listas onde novos itens chegam o tempo todo, `PageNumberPagination` pode
    **repetir ou pular** itens quando algo é inserido entre duas páginas. O
    `CursorPagination` aponta para uma posição estável — ideal para "carregar
    mais" infinito.

### Filtros, busca e ordenação

Os *backends* de filtro leem query params e recortam o queryset antes de
serializar. A busca e a ordenação vêm no próprio DRF; filtros por campo pedem a
lib [`django-filter`](../libs/django-filter.md).

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

Isso habilita, de graça:

```bash
# filtro exato por campo (django-filter)
curl "http://127.0.0.1:8000/api/posts/?status=published&author=3"

# busca textual (SearchFilter)
curl "http://127.0.0.1:8000/api/posts/?search=django"

# ordenação (OrderingFilter)
curl "http://127.0.0.1:8000/api/posts/?ordering=-published_at"
```

!!! info "Prefixos do `SearchFilter`"
    Em `search_fields` você pode prefixar o campo: `^` (começa com), `=`
    (igual exato), `@` (busca full-text no PostgreSQL) e `$` (regex). Sem
    prefixo, é `icontains` (contém, sem diferenciar maiúsculas).

### Versioning: evoluir sem quebrar

Versionamento deixa `request.version` disponível para você mudar comportamento
sem quebrar clientes antigos. Escolha **um** esquema.

| Esquema | Onde vive a versão | Exemplo |
| --- | --- | --- |
| `URLPathVersioning` | No caminho da URL | `/api/v1/posts/` |
| `NamespaceVersioning` | No namespace de URL | `include(..., namespace="v1")` |
| `AcceptHeaderVersioning` | No header `Accept` | `Accept: application/json; version=1.0` |
| `QueryParameterVersioning` | Em query param | `/api/posts/?version=1.0` |
| `HostNameVersioning` | No subdomínio | `v1.api.exemplo.com` |

O mais comum e explícito é o `URLPathVersioning`:

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

Dentro da view, `request.version` diz qual versão o cliente pediu:

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

!!! tip "Escolha um esquema e case a rota"
    O esquema de versionamento precisa combinar com o desenho das URLs:
    `URLPathVersioning` exige o `<version>` no `path`. Fixe `ALLOWED_VERSIONS`
    para o DRF recusar (`404`) versões inexistentes em vez de servir a padrão
    silenciosamente.

### Nested serializers e `drf-nested-routers`

Aninhar objetos na leitura é comum: o post traz autor, tags e comentários.

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

O `SerializerMethodField` é um campo **somente leitura calculado**: o DRF chama
`get_<nome>(self, obj)` e usa o retorno. Perfeito para agregados e derivações
que não existem como coluna.

!!! warning "N+1 mora nos aninhados"
    Cada relação aninhada e cada `SerializerMethodField` que consulta o banco
    pode disparar uma query por objeto. Resolva no `get_queryset` com
    `select_related` (FK) e `prefetch_related` (M2M/reverse), e prefira
    `Count(...)` anotado a `.count()` por item quando a lista é grande.

Para **URLs realmente aninhadas** — `/api/posts/<slug>/comments/` — o router
padrão não basta. Use `drf-nested-routers`:

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

Isso gera `GET /api/posts/<slug>/comments/` e amigos, com o `post_slug` chegando
em `self.kwargs`.

### Validação no serializer

O serializer valida como um `ModelForm`. Há três níveis:

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

- **`validate_<campo>`** — valida um campo isolado.
- **`validate`** — valida o conjunto (regras que cruzam campos).
- **Validators de campo** — como `UniqueValidator`, declarados no campo.

### OpenAPI/Swagger com `drf-spectacular`

Uma API de produção precisa de documentação navegável. O `drf-spectacular`
gera um schema **OpenAPI 3** a partir dos seus serializers e views.

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

Abra **<http://127.0.0.1:8000/api/docs/>** para o Swagger UI interativo, ou
consuma o schema cru em `/api/schema/`.

!!! note "Anote onde o schema não adivinha"
    O `drf-spectacular` infere quase tudo dos serializers, mas para campos
    dinâmicos ou views custom use o decorator `@extend_schema` para descrever
    parâmetros e respostas. Um schema correto vale ouro para clientes gerados
    automaticamente. Veja mais libs em [Bibliotecas afins](../libs/afins.md).

```mermaid
flowchart LR
    C["Cliente"] --> A["Autenticação<br/>(quem é?)"]
    A --> P["Permissão<br/>(pode?)"]
    P --> T["Throttle<br/>(com que frequência?)"]
    T --> V["View / ViewSet"]
    V --> S["Serializer<br/>(valida + JSON)"]
    S --> C
```

!!! quote "📖 Na documentação oficial"
    - [Authentication](https://www.django-rest-framework.org/api-guide/authentication/)
    - [Throttling](https://www.django-rest-framework.org/api-guide/throttling/)
    - [Versioning](https://www.django-rest-framework.org/api-guide/versioning/)

## Recap

- **Autenticação** identifica o cliente: `Session` para front no mesmo domínio,
  `Token` para casos simples, **JWT (simplejwt)** para mobile/SPA com expiração.
- **Permissões** decidem o que cada um pode fazer; escreva
  `has_object_permission` para regras de dono.
- **Throttling** (`Anon`/`User`/`Scoped`) contém abuso via cache — não é
  substituto de rate limiting de borda.
- **Paginação** tem três estilos; `CursorPagination` brilha em feeds grandes.
- **Filtros/busca/ordenação** vêm dos backends (`DjangoFilterBackend`,
  `SearchFilter`, `OrderingFilter`).
- **Versioning**: escolha um esquema (`URLPathVersioning` é o mais explícito) e
  use `request.version` para bifurcar comportamento.
- **Nested serializers** + `SerializerMethodField` para leitura rica;
  `drf-nested-routers` para URLs aninhadas de verdade. Cuidado com N+1.
- **Validação** em três níveis: `validate_<campo>`, `validate` e validators.
- **`drf-spectacular`** gera OpenAPI 3 e um Swagger UI navegável.

Com auth, limites, versões e docs no lugar, sua API está pronta para o mundo.
Volte ao [básico do DRF](drf.md) sempre que precisar, e veja o ecossistema em
[Bibliotecas afins](../libs/afins.md).
