# Referência: a QuerySet API completa

!!! quote "Pensa como criança 🧒"
    Imagine uma **caixa gigante de bolinhas** (todos os registros). Um
    **QuerySet** é um pedido: "me dá só as bolinhas azuis, em ordem de tamanho".
    O truque: enquanto você só descreve o pedido, ninguém abre a caixa. Só quando
    você **pega** as bolinhas para brincar (iterar, contar, listar) é que o
    Django abre a caixa **uma vez** e traz tudo. Isso se chama *preguiça*.

## Caso de uso

Você quer os posts publicados de um autor, mais novos primeiro, já trazendo o
autor junto para não fazer mil consultas:

```python
posts = (
    Post.objects
    .filter(status="published", author__display_name="Ana")
    .order_by("-published_at")
    .select_related("author")
)
# Nenhuma query ainda — só a descrição do pedido.

for post in posts:            # AQUI a caixa abre, uma vez
    print(post.title)
```

Agora o catálogo completo de métodos: quais devolvem **outro QuerySet** (dá para
encadear) e quais devolvem um **valor final** (a caixa abre).

## Possibilidades

### Métodos que retornam QuerySet (encadeáveis, preguiçosos)

| Método | O que faz |
| --- | --- |
| `all()` | Cópia de tudo |
| `filter(**kw)` | Mantém os que casam |
| `exclude(**kw)` | Remove os que casam |
| `order_by(*campos)` | Ordena (`-` = decrescente) |
| `reverse()` | Inverte a ordem |
| `distinct()` | Remove duplicados |
| `values(*campos)` | Dicts em vez de objetos |
| `values_list(*campos)` | Tuplas (ou `flat=True` para lista simples) |
| `annotate(...)` | Adiciona um campo calculado por linha |
| `select_related(*fk)` | JOIN para FK/OneToOne (contra N+1) |
| `prefetch_related(*rel)` | Busca casada para M2M/reverso |
| `only(*campos)` / `defer(*campos)` | Carrega/adia colunas |
| `none()` | QuerySet vazio |
| `union/intersection/difference` | Operações de conjunto |

### Métodos que retornam um valor (a caixa abre aqui)

| Método | Retorna |
| --- | --- |
| `get(**kw)` | **Um** objeto (ou erro `DoesNotExist`/`MultipleObjectsReturned`) |
| `first()` / `last()` | Um objeto ou `None` |
| `count()` | Quantidade (`SELECT COUNT(*)`) |
| `exists()` | `True`/`False` (existe algum?) |
| `aggregate(...)` | Dict com totais (soma, média...) |
| `latest(campo)` / `earliest(campo)` | O mais novo/velho |
| `in_bulk(ids)` | Dict `{id: objeto}` |
| `create(**kw)` | Cria e salva, retorna o objeto |
| `get_or_create(**kw)` | `(objeto, criou?)` |
| `update_or_create(**kw)` | `(objeto, criou?)`, atualizando se existir |
| `bulk_create([...])` | Insere vários numa query |
| `update(**kw)` | Atualiza em massa, retorna nº de linhas |
| `delete()` | Apaga, retorna contagem |

!!! danger "`get()` levanta exceção; `filter().first()` não"
    - `get()` espera **exatamente um**. Zero → `DoesNotExist`; mais de um →
      `MultipleObjectsReturned`.
    - Para "talvez exista", use `filter(...).first()` (dá `None`) ou
      `get_object_or_404(...)` nas views.

### Lookups: o `__` que filtra fino

Pensa como criança: o `__` é a lupa que olha *dentro* do campo.

| Lookup | Significado | Exemplo |
| --- | --- | --- |
| `exact` / `iexact` | Igual / igual sem caixa | `title__iexact="olá"` |
| `contains` / `icontains` | Contém / sem caixa | `title__icontains="django"` |
| `startswith` / `endswith` | Começa/termina com | `slug__startswith="2026"` |
| `in` | Está na lista | `id__in=[1, 2, 3]` |
| `gt` / `gte` / `lt` / `lte` | Maior/menor (ou igual) | `views__gte=100` |
| `range` | Entre dois valores | `published_at__range=(a, b)` |
| `isnull` | É nulo? | `published_at__isnull=True` |
| `date` / `year` / `month` / `day` | Partes de data | `created_at__year=2026` |
| `regex` / `iregex` | Casa regex | `title__regex=r"^\d"` |

```python
Post.objects.filter(title__icontains="orm", created_at__year=2026)
Post.objects.filter(author__user__email__endswith="@empresa.com")   # atravessa relações
```

### Atravessar relações

```python
# posts cuja tag tem slug "django"
Post.objects.filter(tags__slug="django")

# acesso reverso: comentários de posts publicados
Comment.objects.filter(post__status="published")
```

### `F`: comparar/atualizar usando o próprio banco

Pensa como criança: `F` é apontar para **outra gaveta** do mesmo registro, sem
tirar o valor para fora.

```python
from django.db.models import F

# incrementa sem race condition (tudo no banco, uma query)
Post.objects.filter(pk=1).update(views=F("views") + 1)

# posts com mais curtidas que comentários
Post.objects.filter(likes__gt=F("comments_count"))
```

### `Q`: OU, E, NÃO

Pensa como criança: `filter(a=1, b=2)` é sempre "**e**". Quando você quer "**ou**",
chama o `Q`.

```python
from django.db.models import Q

# título contém "django" OU corpo contém "python"
Post.objects.filter(Q(title__icontains="django") | Q(body__icontains="python"))

# publicado E NÃO destacado
Post.objects.filter(Q(status="published") & ~Q(is_featured=True))
```

| Operador | Significado |
| --- | --- |
| `\|` | OU |
| `&` | E |
| `~` | NÃO |

### `annotate` e `aggregate`: contas

- **`aggregate`** → um resultado para o **conjunto todo** (um dict).
- **`annotate`** → um resultado **por linha** (vira um campo extra).

```python
from django.db.models import Avg, Count, Sum

# total geral (aggregate)
Post.objects.aggregate(total=Count("id"), media_views=Avg("views"))
# -> {"total": 42, "media_views": 137.5}

# por linha (annotate): cada post com seu nº de comentários
posts = Post.objects.annotate(n_comments=Count("comments")).order_by("-n_comments")
for p in posts:
    print(p.title, p.n_comments)
```

| Função | Calcula |
| --- | --- |
| `Count` | Contagem |
| `Sum` | Soma |
| `Avg` | Média |
| `Max` / `Min` | Máximo / mínimo |

### Combatendo o N+1 (de novo, porque é o que mais dói)

```python
# FK / OneToOne -> select_related (faz JOIN)
Post.objects.select_related("author")

# M2M / reverso -> prefetch_related (2 queries casadas)
Post.objects.prefetch_related("tags", "comments")
```

!!! danger "Regra de ouro"
    Vai iterar e acessar uma relação? **FK/OneToOne → `select_related`**;
    **M2M/reverso → `prefetch_related`**. Sem isso, 100 objetos viram 101
    queries.

!!! quote "📖 Na documentação oficial"
    - [QuerySet API reference](https://docs.djangoproject.com/en/stable/ref/models/querysets/)
    - [Making queries](https://docs.djangoproject.com/en/stable/topics/db/queries/)

## Recap

- QuerySets são **preguiçosos**: só batem no banco quando você usa os dados.
- Encadeáveis (`filter`, `exclude`, `order_by`, `annotate`, `select_related`) ×
  finais (`get`, `first`, `count`, `exists`, `aggregate`, `update`).
- `get()` levanta exceção; `filter().first()` devolve `None`.
- Lookups com `__` (`icontains`, `gte`, `in`, `year`, `isnull`), atravessam
  relações.
- `F` compara/atualiza dentro do banco; `Q` faz OU/E/NÃO.
- `aggregate` (conjunto) × `annotate` (por linha). E sempre cuide do N+1.

Tudo isso depende de configuração. Veja o mapa em **[settings](settings.md)**.
