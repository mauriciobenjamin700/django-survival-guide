# API REST com DRF

Até aqui, o blog renderiza **HTML** no servidor. Agora vamos expor os **mesmos
modelos** como uma **API REST** em JSON, usando o
[Django REST Framework](https://www.django-rest-framework.org/) (DRF).

!!! quote "A ponte mental"
    O DRF é o espelho da parte web que você já conhece:

    | Web (HTML) | API (DRF) |
    | --- | --- |
    | `ModelForm` | `ModelSerializer` |
    | Template | Serializer (renderiza JSON) |
    | `ListView`/`DetailView` | `ViewSet` |
    | `urls.py` + `path` | `Router` |

    Mesma orientação a objetos, mesma filosofia — só muda o formato de saída.

## Instalação e configuração

```bash
uv add djangorestframework
```

Registre em `INSTALLED_APPS` e configure o comportamento padrão:

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
    Essa permissão padrão libera **leitura** (GET) para qualquer um, mas exige
    **login** para escrever (POST/PUT/DELETE). É o comportamento típico de um
    blog: todos leem, só autores publicam.

## Serializers: validação e JSON

Um `ModelSerializer` deriva os campos do modelo, valida a entrada e serializa a
saída — exatamente como um `ModelForm`, mas para JSON:

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

1. **Leitura**: o autor sai como objeto aninhado (`{"id":.., "display_name":..}`).
2. **Leitura**: as tags saem como lista de objetos.
3. **Escrita**: o cliente manda `tag_ids: [1, 2]` (só os IDs). `source="tags"`
   liga esse campo de escrita à relação real.

!!! tip "Separar leitura de escrita"
    Aninhar objetos é ótimo para *ler* (o cliente recebe tudo mastigado), mas
    ruim para *escrever* (o cliente teria que reenviar o objeto inteiro). O par
    `tags` (read-only aninhado) + `tag_ids` (write-only por PK) resolve os dois
    lados com clareza. `read_only_fields` protege campos derivados, como fizemos
    nos formulários.

## ViewSets: o CRUD em uma classe

Um `ViewSet` é a versão API das generic views: uma classe entrega list,
retrieve, create, update e destroy de uma vez.

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

Repare como os conceitos do tutorial se repetem:

- **`get_queryset()`** — mesma ideia da `ListView`: anônimos só veem publicados;
  logados veem tudo. E resolvemos o N+1 com `select_related`/`prefetch_related`.
- **`perform_create()`** — o equivalente ao `form_valid`: injeta o autor a partir
  do usuário logado, nunca do payload.
- **`lookup_field = "slug"`** — a URL de detalhe usa o slug, não o id.

## Routers: URLs automáticas

Um `DefaultRouter` inspeciona cada ViewSet e **gera todas as rotas REST**:

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

Montado em `/api/` no `urls.py` raiz, isso gera:

| Método + URL | Ação |
| --- | --- |
| `GET /api/posts/` | listar (paginado) |
| `POST /api/posts/` | criar (requer login) |
| `GET /api/posts/<slug>/` | detalhe |
| `PUT/PATCH /api/posts/<slug>/` | atualizar |
| `DELETE /api/posts/<slug>/` | remover |

## Experimentando

Suba o servidor e abra **<http://127.0.0.1:8000/api/>** — o DRF traz uma **API
navegável** no próprio navegador, ótima para explorar.

Via linha de comando:

```bash
# listar (público)
curl http://127.0.0.1:8000/api/posts/

# um post
curl http://127.0.0.1:8000/api/posts/why-class-based-views-scale/
```

A resposta paginada tem o formato:

```json
{
  "count": 4,
  "next": null,
  "previous": null,
  "results": [ { "id": 1, "title": "...", "author": {...}, "tags": [...] } ]
}
```

## Recapitulando

- O DRF expõe os mesmos modelos como JSON, espelhando os conceitos da web.
- **Serializer** = `ModelForm` da API: valida e serializa; proteja campos
  derivados com `read_only_fields`.
- Separe leitura aninhada de escrita por PK (`tags` + `tag_ids`).
- **ViewSet** = CBV da API; `get_queryset`/`perform_create` repetem o que você já
  fazia. Cuide do N+1 aqui também.
- **Router** gera as rotas REST automaticamente e uma API navegável.

Construímos web e API sobre a mesma base. Falta garantir que tudo continue
funcionando conforme o projeto cresce — os **[Testes](testing.md)**.
