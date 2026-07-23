# Referência: campos de modelo (fields)

!!! quote "Pensa como criança 🧒"
    Um **modelo** é uma caixa organizadora. Cada **field** (campo) é uma
    gavetinha dessa caixa: uma guarda *nomes*, outra guarda *números*, outra
    guarda *datas*. Quando você diz "essa gaveta só cabe texto até 200 letras",
    o Django não deixa ninguém enfiar coisa errada lá dentro. Os **fields** são
    as regras de cada gaveta.

## Caso de uso

Você quer guardar posts de um blog. Cada post tem título (texto curto), corpo
(texto longo), uma data e um status. Você descreve isso **uma vez**, como uma
classe, e o Django cria a tabela e valida os dados:

```python
# apps/blog/models.py
from django.db import models


class Post(models.Model):
    """A single blog post."""

    title = models.CharField(max_length=200)
    body = models.TextField()
    published_at = models.DateTimeField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
```

Pronto: quatro gavetas, cada uma com sua regra. Agora vamos ver **todas as
gavetas possíveis** e **todos os botões de ajuste** de cada uma.

## Possibilidades

### Opções comuns a (quase) todos os fields

Estes botões existem em praticamente qualquer field. São o que mais confunde na
doc oficial — aqui, um de cada vez.

| Opção | O que faz | Padrão |
| --- | --- | --- |
| `null` | A coluna aceita `NULL` no **banco** | `False` |
| `blank` | O campo pode ficar vazio na **validação de formulário** | `False` |
| `default` | Valor usado quando nada é informado (valor ou callable) | — |
| `unique` | Nenhum outro registro pode ter o mesmo valor | `False` |
| `db_index` | Cria um índice na coluna (buscas mais rápidas) | `False` |
| `primary_key` | Torna este campo a chave primária | `False` |
| `editable` | Se `False`, some dos formulários e do admin | `True` |
| `choices` | Restringe a uma lista de opções | — |
| `validators` | Lista de funções que validam o valor | `[]` |
| `verbose_name` | Nome "bonito" exibido ao usuário | nome do campo |
| `help_text` | Textinho de ajuda no formulário | `""` |
| `error_messages` | Personaliza as mensagens de erro | — |
| `db_column` | Nome da coluna no banco (se diferente do atributo) | nome do atributo |
| `db_comment` | Comentário na coluna, guardado no banco | — |

!!! danger "`null` × `blank`: a confusão nº 1 do Django"
    - **`null`** é sobre o **banco de dados**: a coluna aceita "nada" (`NULL`).
    - **`blank`** é sobre **formulários**: o usuário pode deixar em branco.

    Pensa como criança: `null` é "a gaveta pode ficar *fisicamente* vazia";
    `blank` é "o adulto *permite* você não preencher".

    Regra prática: para **texto** (`CharField`, `TextField`), use só
    `blank=True` e **nunca** `null=True` — assim "vazio" é sempre `""`, e você
    não tem dois jeitos de dizer "nada" (`""` e `None`). Para números, datas e
    relações, aí sim `null=True` faz sentido quando o valor é opcional.

#### `default`: valor ou função

```python
from django.utils import timezone

class Post(models.Model):
    created_at = models.DateTimeField(default=timezone.now)  # (1)!
    views = models.IntegerField(default=0)
    tags_cache = models.JSONField(default=list)              # (2)!
```

1. Passe a **função** (`timezone.now`), sem parênteses. O Django chama na hora
   de criar. Se você pusesse `timezone.now()`, o valor seria congelado no
   momento em que o servidor iniciou. 😱
2. Para listas/dicts como default, passe o **callable** (`list`, `dict`), nunca
   `[]` ou `{}` literais — senão todos os registros compartilhariam o mesmo
   objeto.

#### `choices`: a forma moderna com `TextChoices`

```python
class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Rascunho"        # (valor no banco, rótulo exibido)
        PUBLISHED = "published", "Publicado"

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )
```

!!! tip "Por que `TextChoices` e não uma lista solta"
    `Status.PUBLISHED` é legível, tipado e autocompletável. E o Django te dá de
    graça um método `post.get_status_display()` que devolve o rótulo bonito
    (`"Publicado"`). Nunca espalhe strings mágicas (`"published"`) pelo código.

### Fields de texto

| Field | Guarda | Opção-chave |
| --- | --- | --- |
| `CharField` | Texto curto | `max_length` (obrigatório) |
| `TextField` | Texto longo | — |
| `SlugField` | Texto para URL (letras, números, hífen) | `max_length`, `allow_unicode` |
| `EmailField` | E-mail (valida formato) | `max_length` |
| `URLField` | URL (valida formato) | `max_length` |
| `UUIDField` | UUID | costuma vir com `default=uuid.uuid4` |

```python
import uuid

class Article(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    body = models.TextField(blank=True)
    contact = models.EmailField(blank=True)
```

### Fields numéricos

| Field | Guarda |
| --- | --- |
| `IntegerField` | Inteiro |
| `BigIntegerField` | Inteiro grande (64 bits) |
| `PositiveIntegerField` | Inteiro ≥ 0 |
| `SmallIntegerField` | Inteiro pequeno |
| `FloatField` | Ponto flutuante |
| `DecimalField` | Decimal exato (dinheiro!) — exige `max_digits` e `decimal_places` |

```python
class Product(models.Model):
    stock = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=8, decimal_places=2)  # até 999999.99
```

!!! warning "Dinheiro é `DecimalField`, nunca `FloatField`"
    `FloatField` tem erro de arredondamento (`0.1 + 0.2 != 0.3`). Para preço,
    saldo, qualquer valor monetário: `DecimalField`. `max_digits` é o total de
    dígitos; `decimal_places`, quantos vêm depois da vírgula.

### Fields de data e hora

| Field | Guarda | Opções especiais |
| --- | --- | --- |
| `DateField` | Só a data | `auto_now`, `auto_now_add` |
| `DateTimeField` | Data + hora | `auto_now`, `auto_now_add` |
| `TimeField` | Só a hora | `auto_now`, `auto_now_add` |
| `DurationField` | Um intervalo de tempo | — |

```python
class Post(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)  # grava só ao criar
    updated_at = models.DateTimeField(auto_now=True)      # atualiza a cada save
```

!!! info "`auto_now_add` × `auto_now`"
    - **`auto_now_add=True`**: carimba a data **uma vez**, na criação. Nunca mais
      muda. (Bom para `created_at`.)
    - **`auto_now=True`**: atualiza **toda vez** que você salva. (Bom para
      `updated_at`.)

    Pensa como criança: `auto_now_add` é a data de nascimento (não muda);
    `auto_now` é "última vez que mexeram no brinquedo".

### Fields booleanos

```python
class Post(models.Model):
    is_published = models.BooleanField(default=False)
    reviewed = models.BooleanField(null=True)  # 3 estados: sim / não / ainda-não-sei
```

### Fields de arquivo

| Field | Guarda | Precisa de |
| --- | --- | --- |
| `FileField` | Caminho de um arquivo enviado | `upload_to`, `MEDIA_ROOT` configurado |
| `ImageField` | Igual, mas valida que é imagem | `Pillow` instalado |

```python
class Profile(models.Model):
    avatar = models.ImageField(upload_to="avatars/%Y/%m/", blank=True)
```

### Fields de relação

O coração do ORM. Detalhados em [Modelos e o ORM](../tutorial/models.md), aqui o
resumo das opções:

| Field | Relação | Opções principais |
| --- | --- | --- |
| `ForeignKey` | Muitos-para-um | `on_delete` (obrigatório), `related_name`, `related_query_name`, `limit_choices_to` |
| `OneToOneField` | Um-para-um | `on_delete` (obrigatório), `related_name` |
| `ManyToManyField` | Muitos-para-muitos | `related_name`, `through`, `symmetrical`, `blank` |

```python
class Post(models.Model):
    author = models.ForeignKey(
        "Author",
        on_delete=models.CASCADE,     # o que fazer se o autor for apagado
        related_name="posts",         # author.posts.all()
        limit_choices_to={"is_active": True},  # só autores ativos no dropdown
    )
    tags = models.ManyToManyField("Tag", related_name="posts", blank=True)
```

Valores de `on_delete`:

| Valor | Ao apagar o referenciado... |
| --- | --- |
| `CASCADE` | Apaga junto os dependentes |
| `PROTECT` | Bloqueia o apagamento (levanta erro) |
| `RESTRICT` | Bloqueia, mas permite se outra relação em cascata cuidar |
| `SET_NULL` | Zera a referência (exige `null=True`) |
| `SET_DEFAULT` | Volta ao `default` |
| `SET(valor)` | Define um valor/callable específico |
| `DO_NOTHING` | Não faz nada (cuidado: pode quebrar integridade) |

!!! danger "`on_delete` é obrigatório em `ForeignKey`/`OneToOneField`"
    Sem ele, o Django nem deixa criar o modelo. Pergunte-se sempre: "se o pai
    sumir, o que acontece com o filho?"

!!! quote "📖 Na documentação oficial"
    - [Model field reference](https://docs.djangoproject.com/en/stable/ref/models/fields/)

## Recap

- Um **field** é uma gaveta com regras. `CharField`, `IntegerField`,
  `DateTimeField`, `ForeignKey`... cada tipo guarda uma coisa.
- Opções comuns: `null` (banco) × `blank` (formulário), `default` (passe
  *callable*, não literal), `unique`, `db_index`, `choices` (use `TextChoices`),
  `verbose_name`, `help_text`.
- Texto vazio: só `blank=True`. Dinheiro: `DecimalField`. Datas automáticas:
  `auto_now_add` (criação) × `auto_now` (todo save).
- Relações exigem `on_delete` e ganham `related_name` para o acesso reverso.

Definidas as gavetas, você ajusta o comportamento da **caixa inteira** na
[Meta do modelo](models-meta.md).
