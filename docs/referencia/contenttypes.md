# Referência: content types e relações genéricas

!!! quote "Pensa como criança 🧒"
    Um comentário normal gruda em **um** tipo de coisa (um post). Mas e se você
    quisesse um "curtir" que gruda em **qualquer** coisa — um post, uma foto, um
    comentário? Uma relação genérica é uma **fita adesiva universal**: em vez de
    apontar para uma gaveta específica, ela anota "que tipo de coisa" + "qual id"
    e cola em qualquer modelo.

## Caso de uso

Você quer um modelo `Like` que funcione para posts **e** comentários **e** o que
vier no futuro — sem uma FK para cada tipo. A relação genérica resolve:

```python
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Like(models.Model):
    """A 'like' that can point at any model instance."""

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)  # (1)!
    object_id = models.PositiveIntegerField()                                # (2)!
    target = GenericForeignKey("content_type", "object_id")                  # (3)!
    created_at = models.DateTimeField(auto_now_add=True)
```

1. **Qual tipo** de objeto (Post? Comment?).
2. **Qual id** daquele tipo.
3. O atalho que junta os dois num acesso natural: `like.target`.

```python
post = Post.objects.get(pk=1)
Like.objects.create(target=post)      # curtiu um post
like.target                            # devolve o Post de volta
```

## Possibilidades

### O que é o `ContentType`

Pensa como criança: o Django mantém uma **lista de todos os modelos** do projeto,
cada um com um número. `ContentType` é essa tabela de "tipos de coisa".

```python
from django.contrib.contenttypes.models import ContentType

ct = ContentType.objects.get_for_model(Post)
ct.app_label      # "blog"
ct.model          # "post"
ct.model_class()  # <class 'apps.blog.models.Post'>
```

### As três peças de uma `GenericForeignKey`

| Peça | Guarda |
| --- | --- |
| `content_type` (FK para `ContentType`) | *Qual modelo* |
| `object_id` (inteiro) | *Qual linha* daquele modelo |
| `GenericForeignKey(...)` | O atalho que resolve os dois em um objeto |

!!! info "Precisa do app `contenttypes`"
    O `django.contrib.contenttypes` já vem em `INSTALLED_APPS` no
    `startproject` — é dependência do sistema de permissões e do admin. Nada a
    instalar.

### O caminho de volta: `GenericRelation`

A `GenericForeignKey` te leva do `Like` ao alvo. Para ir do **alvo** aos likes
(`post.likes.all()`), o modelo alvo declara uma `GenericRelation`:

```python
from django.contrib.contenttypes.fields import GenericRelation


class Post(models.Model):
    likes = GenericRelation(Like, related_query_name="post")

# agora dá para o caminho reverso e para filtrar
post.likes.count()
Post.objects.filter(likes__isnull=False)     # posts que têm likes
```

### Índice recomendado

!!! tip "Indexe o par (content_type, object_id)"
    Consultas genéricas quase sempre filtram pelos dois campos juntos. Um índice
    combinado acelera muito:
    ```python
    class Like(models.Model):
        # ... campos ...
        class Meta:
            indexes = [models.Index(fields=["content_type", "object_id"])]
    ```

### Quando NÃO usar relação genérica

!!! danger "Genérico custa: sem integridade e sem JOIN limpo"
    A fita universal é flexível, mas paga um preço:

    - **Sem chave estrangeira real** → o banco não garante que o `object_id`
      existe (nada de `CASCADE`/`PROTECT` automáticos).
    - **Consultas mais pesadas** → não dá para um `JOIN` direto; filtrar/ordenar
      pelo alvo é chato.

    Se você tem **poucos** tipos-alvo conhecidos (só Post e Comment), muitas vezes
    é melhor **duas FKs normais** (com `null=True` e um `CheckConstraint`
    garantindo que exatamente uma está preenchida). Use relação genérica quando o
    conjunto de alvos é **aberto/desconhecido** (curtidas, tags, comentários,
    anexos, logs de auditoria).

### Quem usa por baixo dos panos

O próprio Django usa `contenttypes` internamente: o sistema de **permissões**
(`Permission` aponta para um `ContentType`) e o `LogEntry` do **admin** (registra
ações sobre qualquer modelo). Bibliotecas como `django-taggit` e sistemas de
comentários genéricos também.

## Recap

- `ContentType` é a tabela de "todos os modelos"; `get_for_model(X)` te dá o tipo.
- Relação genérica = `content_type` + `object_id` + `GenericForeignKey` → aponta
  para **qualquer** modelo (`like.target`).
- `GenericRelation` no alvo dá o caminho reverso (`post.likes`) e permite filtrar.
- Indexe `(content_type, object_id)`.
- Custo: sem integridade referencial nem JOIN limpo. Poucos alvos → prefira FKs
  normais; alvos abertos → relação genérica.

Muitos dados pedem contas por grupo. Veja
**[agregação e group by](aggregation-groupby.md)**.
