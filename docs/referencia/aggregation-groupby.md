# Referência: agregação e "group by"

!!! quote "Pensa como criança 🧒"
    Imagine uma caixa de bolinhas coloridas. **Agregar** é responder perguntas de
    resumo: "quantas bolinhas ao todo?", "qual o tamanho médio?". **Group by** é
    fazer essa conta **por cor**: "quantas azuis, quantas vermelhas". O Django faz
    o banco calcular isso — você não conta na mão.

## Caso de uso

Quantos posts cada autor tem, e a média de comentários por post — em uma query,
sem trazer nada para o Python:

```python
from django.db.models import Avg, Count

# por autor (group by)
autores = Author.objects.annotate(n_posts=Count("posts"))
for a in autores:
    print(a.display_name, a.n_posts)

# resumo geral
resumo = Post.objects.aggregate(total=Count("id"), media=Avg("views"))
# -> {"total": 42, "media": 137.5}
```

## Possibilidades

### `aggregate` × `annotate`: a diferença que confunde

Pensa como criança:

- **`aggregate`** = uma resposta para a **caixa inteira** (um dicionário).
- **`annotate`** = uma resposta para **cada bolinha/grupo** (vira coluna extra).

```python
# aggregate: UM número para todos os posts
Post.objects.aggregate(total=Count("id"))         # {"total": 42}

# annotate: um número POR autor
Author.objects.annotate(n=Count("posts"))          # cada autor ganha .n
```

| | `aggregate` | `annotate` |
| --- | --- | --- |
| Retorna | Um `dict` | Um queryset |
| Granularidade | O conjunto todo | Por linha/grupo |
| Encadeia? | Não (é terminal) | Sim |

### As funções de agregação

| Função | Calcula |
| --- | --- |
| `Count` | Quantidade |
| `Sum` | Soma |
| `Avg` | Média |
| `Max` / `Min` | Máximo / mínimo |
| `StdDev` / `Variance` | Desvio / variância |

### Como o "group by" realmente acontece

Pensa como criança: o "por cor" surge quando você diz **por qual campo agrupar**.
No Django, isso vem de `values()` antes do `annotate()`:

```python
# quantos posts POR status  (group by status)
(
    Post.objects
    .values("status")                    # (1)!  <- define o grupo
    .annotate(n=Count("id"))             # (2)!  <- a conta por grupo
    .order_by("-n")
)
# -> [{"status": "published", "n": 30}, {"status": "draft", "n": 12}]
```

1. `values("status")` diz "agrupe por status".
2. `annotate` calcula dentro de cada grupo.

!!! danger "A ORDEM importa: `values()` ANTES de `annotate()`"
    - `values("campo").annotate(...)` → **group by campo** (uma linha por valor).
    - `annotate(...).values("campo")` → anota **por linha** e depois escolhe
      colunas (NÃO agrupa).

    Trocar a ordem muda completamente o resultado. Para "group by", `values`
    **primeiro**.

### Agregação condicional (contar só o que casa)

```python
from django.db.models import Count, Q

Author.objects.annotate(
    total=Count("posts"),
    publicados=Count("posts", filter=Q(posts__status="published")),
)
```

O `filter=Q(...)` conta apenas as linhas que batem — dois números na mesma query.

### Cuidado: agregar por múltiplas relações

!!! warning "Contagens infladas ao juntar duas relações"
    `Author.objects.annotate(n_posts=Count("posts"), n_comments=Count("comments"))`
    pode **inflar** os números: o JOIN multiplica linhas (cada post cruza com
    cada comentário). A correção é `distinct=True`:
    ```python
    Count("posts", distinct=True)
    ```
    Sintoma: números "grandes demais" quando você agrega duas relações de uma vez.

### Filtrar por resultado de agregação: use `filter` depois do `annotate`

Pensa como criança: o "HAVING" do SQL. Filtre **depois** de anotar:

```python
# autores com mais de 5 posts
Author.objects.annotate(n=Count("posts")).filter(n__gt=5)
```

- `filter()` **antes** do `annotate()` → filtra as linhas que entram na conta.
- `filter()` **depois** → filtra pelos grupos já contados (o "HAVING").

### `values_list` para resultados enxutos

```python
# lista de (status, contagem)
Post.objects.values("status").annotate(n=Count("id")).values_list("status", "n")
# -> [("published", 30), ("draft", 12)]
```

!!! quote "📖 Na documentação oficial"
    - [Aggregation](https://docs.djangoproject.com/en/stable/topics/db/aggregation/)

## Recap

- `aggregate` = um resumo do conjunto (dict); `annotate` = uma coluna por
  linha/grupo (queryset).
- "Group by" = `values("campo")` **antes** de `annotate()` — a ordem é o segredo.
- Agregação condicional com `Count(..., filter=Q(...))`.
- Agregou duas relações e o número inflou? Use `distinct=True`.
- Filtrar por total é `annotate(...).filter(...)` (o "HAVING").

Arquivos enviados por usuários precisam de um lugar para morar: os
**[storages](storages.md)**.
