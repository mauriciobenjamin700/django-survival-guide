# Referência: DRF — serializers e viewsets

!!! quote "Pensa como criança 🧒"
    O navegador humano quer uma página bonita (HTML). Mas um app de celular ou
    outro programa quer os dados "pelados", em **JSON** — só a informação, sem
    enfeite. O **serializer** é o tradutor que veste e despe: transforma seu
    objeto Python em JSON (para mandar) e o JSON de volta em objeto (ao receber),
    conferindo se veio certo. O **viewset** é o garçom dessa cozinha de JSON.

## Caso de uso

Você já tem o blog em HTML. Agora um app mobile quer listar e criar posts via
API. Com o DRF, você reaproveita os **mesmos modelos** e expõe JSON com pouquíssimo
código:

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

Um router transforma o viewset em todas as rotas REST. Vamos aos detalhes.

## Possibilidades

!!! info "O espelho da web que você já conhece"
    | Web (HTML) | API (DRF) |
    | --- | --- |
    | `ModelForm` | `ModelSerializer` |
    | Template | Serializer (renderiza JSON) |
    | `ListView` / `DetailView` | `ViewSet` |
    | `urls.py` + `path` | `Router` |

    Mesmos conceitos, formato diferente. Se você entendeu forms e views,
    entende DRF.

### Tipos de serializer

| Classe | Quando usar |
| --- | --- |
| `Serializer` | Controle total; você declara cada field (sem modelo) |
| `ModelSerializer` | Deriva os fields de um modelo (o comum) |
| `HyperlinkedModelSerializer` | Como o acima, mas relações viram URLs |

### A `Meta` do `ModelSerializer`

| Opção | O que faz |
| --- | --- |
| `model` | Qual modelo serializar |
| `fields` | Lista de campos (ou `"__all__"`) |
| `exclude` | Campos a remover (oposto de `fields`) |
| `read_only_fields` | Campos que saem no JSON mas **não** são aceitos na escrita |
| `extra_kwargs` | Ajustes por campo sem redeclarar o field inteiro |
| `depth` | Expande relações aninhadas automaticamente até N níveis |

```python
class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ["id", "title", "slug", "body", "status", "author"]
        read_only_fields = ["slug"]
        extra_kwargs = {
            "body": {"help_text": "Conteúdo em Markdown."},
            "status": {"required": False},
        }
```

!!! danger "`read_only_fields` protege campos derivados"
    Campos como `slug`, `published_at`, `created_at` são calculados no servidor.
    Se o cliente pudesse enviá-los, forjaria dados. Marque-os `read_only`. Mesmo
    princípio do `fields` explícito nos formulários: **não confie no cliente**.

### Opções de field do serializer

Valem para fields declarados manualmente:

| Opção | O que faz |
| --- | --- |
| `read_only` | Só leitura (sai no JSON, não entra) |
| `write_only` | Só escrita (entra, não sai — ex.: senha) |
| `required` | Obrigatório na entrada |
| `default` | Valor padrão se ausente |
| `allow_null` | Aceita `null` |
| `allow_blank` | Aceita string vazia |
| `source` | Liga o field a outro atributo/relação do objeto |
| `validators` | Lista de validadores |
| `help_text` | Documentação (aparece na API navegável) |

### Leitura aninhada × escrita por id (o truque essencial)

Pensa como criança: para **mostrar** o autor, você quer o cartão completo dele.
Para **escolher** o autor, basta apontar o dedo ("esse aqui, número 3"). São
coisas diferentes:

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

1. **Ler**: o autor sai como objeto completo aninhado.
2. **Ler**: as tags saem como lista de objetos.
3. **Escrever**: o cliente manda só `tag_ids: [1, 3]`. `source="tags"` liga esse
   campo de escrita à relação real.

### Validação no serializer

Igualzinho aos forms, com outros nomes:

```python
class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "author_name", "email", "body"]

    def validate_body(self, value: str) -> str:
        """Validate one field: reject too-short comments."""
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Comentário curto demais.")
        return value

    def validate(self, attrs: dict) -> dict:
        """Validate across fields."""
        if attrs["author_name"].lower() in attrs["body"].lower():
            raise serializers.ValidationError("Não repita seu nome no corpo.")
        return attrs
```

| Web (form) | API (serializer) |
| --- | --- |
| `clean_<campo>()` | `validate_<campo>(self, value)` |
| `clean()` | `validate(self, attrs)` |

### Tipos de viewset

| Classe | O que entrega |
| --- | --- |
| `ViewSet` | Nada pronto; você escreve cada ação |
| `GenericViewSet` | Base + mixins que você escolhe |
| `ReadOnlyModelViewSet` | Só `list` + `retrieve` (leitura) |
| `ModelViewSet` | CRUD completo: list, retrieve, create, update, destroy |

### Atributos e ganchos do viewset

| Atributo/método | O que faz |
| --- | --- |
| `queryset` | A base de objetos |
| `serializer_class` | Qual serializer usar |
| `lookup_field` | Campo da URL de detalhe (padrão `"pk"`; use `"slug"`) |
| `permission_classes` | Quem pode acessar |
| `authentication_classes` | Como identificar o cliente |
| `get_queryset()` | Filtrar a base dinamicamente (por usuário, query param) |
| `get_serializer_class()` | Escolher serializer por ação |
| `perform_create(serializer)` | Agir ao criar (equivale ao `form_valid`) |
| `perform_update(serializer)` | Agir ao atualizar |

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

### Ações extras: `@action`

Quer um endpoint além do CRUD (ex.: `/posts/<slug>/publish/`)? Use `@action`:

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

| `@action(...)` | Significado |
| --- | --- |
| `detail=True` | Age sobre **um** objeto (`/posts/<slug>/publish/`) |
| `detail=False` | Age sobre a coleção (`/posts/featured/`) |
| `methods=[...]` | Métodos HTTP aceitos |

### Router: as URLs de graça

```python
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("posts", PostViewSet, basename="post")
```

Isso gera automaticamente:

| Método + URL | Ação |
| --- | --- |
| `GET /posts/` | `list` |
| `POST /posts/` | `create` |
| `GET /posts/<slug>/` | `retrieve` |
| `PUT/PATCH /posts/<slug>/` | `update` |
| `DELETE /posts/<slug>/` | `destroy` |
| `POST /posts/<slug>/publish/` | a `@action` acima |

### Permissões prontas

| Classe | Libera |
| --- | --- |
| `AllowAny` | Todos |
| `IsAuthenticated` | Só logados |
| `IsAuthenticatedOrReadOnly` | Todos leem; só logados escrevem |
| `IsAdminUser` | Só staff |
| `DjangoModelPermissions` | Segue as permissões do modelo no Django |

## Recap

- O serializer é o tradutor Python ↔ JSON; o viewset é o garçom da API.
- DRF espelha a web: `ModelSerializer`≈`ModelForm`, `ViewSet`≈CBV, `Router`≈urls.
- Na `Meta`: `fields` explícito, `read_only_fields` para proteger derivados,
  `extra_kwargs` para ajustes finos.
- Leitura aninhada (`author`/`tags`) × escrita por id (`tag_ids` com `source`).
- Validação: `validate_<campo>` (um) e `validate` (vários) — espelho do `clean`.
- `get_queryset`/`perform_create` são os ganchos (como `get_queryset`/`form_valid`).
- `@action` adiciona endpoints extras; o `Router` gera as URLs REST sozinho.

Você tem agora a referência das quatro camadas. Volte ao
[Tutorial](../tutorial/project-setup.md) para vê-las trabalhando juntas.
