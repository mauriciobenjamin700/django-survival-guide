# Referência: ORM avançado (expressions)

!!! quote "Pensa como criança 🧒"
    Você já sabe pedir bolinhas por cor (`filter`). Agora imagine pedir contas
    **prontas**: "me diga, para cada caixa, quantas bolinhas azuis tem, e marque
    as caixas com mais de 10 como 'cheias'". Em vez de trazer tudo e contar em
    Python, você manda o **banco** fazer a conta — ele é rápido nisso. As
    *expressions* são a linguagem para pedir essas contas.

## Caso de uso

Você quer, numa query só, cada post com seu número de comentários e um rótulo
"popular/normal" — sem trazer nada para o Python e contar na mão:

```python
from django.db.models import Case, Count, Value, When

posts = (
    Post.objects
    .annotate(n_comments=Count("comments"))
    .annotate(
        label=Case(
            When(n_comments__gte=10, then=Value("popular")),
            default=Value("normal"),
        )
    )
)
for p in posts:
    print(p.title, p.n_comments, p.label)   # tudo já veio pronto do banco
```

## Possibilidades

### `Case`/`When`: o "if/else" do banco

Pensa como criança: uma fila de perguntas "se... então...", com um "senão" no
final.

```python
from django.db.models import Case, When, Value, IntegerField

Post.objects.annotate(
    priority=Case(
        When(status="published", then=Value(1)),
        When(status="draft", then=Value(2)),
        default=Value(9),
        output_field=IntegerField(),
    )
).order_by("priority")
```

!!! tip "`output_field` quando o tipo é ambíguo"
    Se o Django não consegue inferir o tipo do resultado (misturando tipos), passe
    `output_field=IntegerField()` (ou `CharField`, etc.) para ele não reclamar.

### Agregação condicional: contar só o que casa

```python
from django.db.models import Count, Q

Author.objects.annotate(
    total=Count("posts"),
    publicados=Count("posts", filter=Q(posts__status="published")),
)
```

O `filter=Q(...)` dentro do `Count` conta **apenas** as linhas que batem — dois
números diferentes na mesma query.

### `Subquery` e `OuterRef`: uma consulta dentro da outra

Pensa como criança: para cada caixa, você faz uma perguntinha extra "qual a
bolinha mais nova **desta** caixa?". O `OuterRef` é o dedo apontando para a caixa
de fora.

```python
from django.db.models import OuterRef, Subquery

ultimo_comentario = (
    Comment.objects
    .filter(post=OuterRef("pk"))       # "deste post" (o de fora)
    .order_by("-created_at")
    .values("author_name")[:1]
)

Post.objects.annotate(ultimo_autor=Subquery(ultimo_comentario))
```

- **`OuterRef("pk")`** aponta para o objeto da query externa.
- **`Subquery(...)[:1]`** traz **um** valor por linha externa.

### `Exists`: "tem algum?" eficiente

```python
from django.db.models import Exists, OuterRef

tem_comentario = Comment.objects.filter(post=OuterRef("pk"))
Post.objects.annotate(comentado=Exists(tem_comentario)).filter(comentado=True)
```

!!! tip "`Exists` é mais rápido que `Count > 0`"
    Para saber apenas *se existe*, `Exists` para na primeira linha; `Count`
    percorre tudo. Use `Exists` quando você só quer sim/não.

### Database functions: contas e textos no banco

```python
from django.db.models import Value
from django.db.models.functions import Coalesce, Concat, Lower, Length, TruncMonth

# junta nome + sobrenome no banco
Author.objects.annotate(full=Concat("first_name", Value(" "), "last_name"))

# usa um padrão quando o valor é nulo
Post.objects.annotate(quando=Coalesce("published_at", "created_at"))

# agrupa por mês
Post.objects.annotate(mes=TruncMonth("published_at")).values("mes").annotate(n=Count("id"))
```

| Função | O que faz |
| --- | --- |
| `Coalesce(a, b)` | Primeiro valor não-nulo |
| `Concat(...)` | Junta textos |
| `Lower` / `Upper` | Caixa do texto |
| `Length` | Tamanho do texto |
| `Trunc*` (`TruncDate`/`TruncMonth`...) | Corta a data para agrupar |
| `Cast` | Converte tipo |
| `Now` | Data/hora do banco |

### `F`: aritmética e comparação entre colunas

```python
from django.db.models import F

# incrementar sem race condition (no banco)
Post.objects.filter(pk=1).update(views=F("views") + 1)

# comparar duas colunas do mesmo registro
Post.objects.filter(likes__gt=F("dislikes"))
```

### Window functions: ranking sem perder as linhas

Pensa como criança: numerar as bolinhas de cada caixa **sem** juntar elas num
montinho — cada bolinha continua ali, só ganha um número.

```python
from django.db.models import F, Window
from django.db.models.functions import RowNumber, Rank

Post.objects.annotate(
    posicao=Window(
        expression=RowNumber(),
        partition_by=[F("author")],        # reinicia a contagem por autor
        order_by=F("published_at").desc(),
    )
)
```

| Função de janela | Dá |
| --- | --- |
| `RowNumber` | Número sequencial (1,2,3...) |
| `Rank` / `DenseRank` | Ranking (com/sem buracos em empates) |
| `Lag` / `Lead` | Valor da linha anterior/seguinte |

!!! danger "Expressions rodam no BANCO, não em Python"
    Toda a graça é o banco fazer a conta e devolver pronto — uma query só, sem
    N+1, sem laço em Python. Se você se pegar trazendo objetos e somando/contando
    num `for`, quase sempre dá para empurrar isso para uma expression.

!!! quote "📖 Na documentação oficial"
    - [Query expressions](https://docs.djangoproject.com/en/stable/ref/models/expressions/)
    - [Database functions](https://docs.djangoproject.com/en/stable/ref/models/database-functions/)

## Recap

- Expressions pedem contas ao **banco**: uma query, resultado pronto.
- `Case`/`When` = if/else; `Count(filter=Q(...))` = agregação condicional.
- `Subquery`+`OuterRef` = consulta correlacionada por linha; `Exists` = sim/não
  eficiente.
- Database functions (`Coalesce`, `Concat`, `Trunc*`, `Cast`) transformam dados
  no banco; `F` faz aritmética/comparação entre colunas.
- Window functions ranqueiam/numeram sem colapsar as linhas.
- Regra: contou/somou num `for` Python? Provavelmente cabe uma expression.

Contas dominadas. Garanta que nada quebra ao evoluir: **[testes a fundo](testing.md)**.
