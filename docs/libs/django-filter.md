# django-filter

Listagens quase sempre precisam de filtros: "posts da tag django", "pedidos entre
duas datas", "produtos acima de R$ 50". Escrever isso na mão em cada view cansa. O
**django-filter** transforma **query params** da URL (`?tag=django&preco__gt=50`)
em filtros de queryset — no Django e no DRF.

!!! quote "Pensa como criança 🧒"
    Imagine uma caixa gigante de brinquedos e uma **peneira** com furos que você
    escolhe: "só os vermelhos", "só os grandes". O django-filter é essa peneira
    configurável: o usuário escolhe os furos pela URL, e só o que passa aparece.

## Instalação

```bash
uv add django-filter
```

```python
# settings.py
INSTALLED_APPS = ["django_filters", ...]
```

## Possibilidades

### Um FilterSet: declarar os furos da peneira

```python
# apps/blog/filters.py
import django_filters

from apps.blog.models import Post


class PostFilter(django_filters.FilterSet):
    """Declarative filters for the Post list."""

    title = django_filters.CharFilter(lookup_expr="icontains")   # (1)!
    tag = django_filters.CharFilter(field_name="tags__slug")     # (2)!
    published_after = django_filters.DateFilter(
        field_name="published_at", lookup_expr="gte",
    )

    class Meta:
        model = Post
        fields = ["status"]        # (3)!
```

1. `?title=orm` casa qualquer título contendo "orm" (case-insensitive).
2. `?tag=django` atravessa a relação até `tags.slug`.
3. Filtros "exatos" automáticos: `?status=published`. Você lista o campo, o
    django-filter cria o filtro.

### No DRF (o uso mais comum)

```python
# settings.py
REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
}
```

```python
# apps/blog/api/views.py
from django_filters.rest_framework import DjangoFilterBackend


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PostFilter        # (1)!
```

1. Ou o atalho `filterset_fields = ["status", "author"]` para filtros exatos sem
    escrever um FilterSet.

Agora a API aceita: `GET /api/posts/?status=published&tag=django&published_after=2026-01-01`.

### Em views baseadas em classe (HTML)

```python
from django_filters.views import FilterView


class PostListView(FilterView):
    model = Post
    filterset_class = PostFilter
    template_name = "blog/post_list.html"
```

```django
<form method="get">
  {{ filter.form.as_p }}      {# gera os campos de filtro #}
  <button type="submit">Filtrar</button>
</form>
{% for post in filter.qs %}{{ post.title }}{% endfor %}
```

!!! tip "Filtro usa GET, não POST"
    Filtro é uma **busca** — os critérios vão na URL (`?tag=...`), então dá para
    compartilhar o link e paginar mantendo o filtro. Por isso o `<form
    method="get">`. Combina com [paginação](../tutorial/pagination.md).

### Tipos de filtro comuns

| Filtro | Para |
| --- | --- |
| `CharFilter` | Texto (com `lookup_expr="icontains"` para "contém") |
| `NumberFilter` | Números (`lookup_expr="gte"/"lte"`) |
| `DateFilter` / `DateFromToRangeFilter` | Data / intervalo de datas |
| `BooleanFilter` | Sim/não |
| `ChoiceFilter` | Lista fixa de opções |
| `ModelChoiceFilter` | Escolher um objeto relacionado |
| `OrderingFilter` | Deixar o cliente ordenar (`?ordering=-published_at`) |

!!! warning "Restrinja o que pode ser filtrado/ordenado"
    Não exponha campos internos sem querer. Liste explicitamente os filtros; para
    ordenação, use `OrderingFilter(fields=[...])` com uma lista fechada — senão o
    cliente ordena por qualquer coluna, o que pode vazar informação ou pesar o
    banco.

## Recapitulando

- django-filter vira **query params** (`?campo=valor`) em filtros de queryset,
  declarados num `FilterSet`.
- Cada filtro define `field_name` (o campo, atravessa `__`) e `lookup_expr`
  (`icontains`, `gte`...).
- No DRF: `DjangoFilterBackend` + `filterset_class` (ou `filterset_fields`).
- No HTML: `FilterView` + `{{ filter.form }}`; filtro usa **GET** e casa com
  paginação.
- Restrinja campos filtráveis/ordenáveis explicitamente.

!!! quote "📖 Na documentação oficial"
    - [django-filter](https://django-filter.readthedocs.io/)

Falta conhecer as ferramentas que todo projeto acaba usando:
**[o catálogo de afins](afins.md)**.
