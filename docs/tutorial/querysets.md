# QuerySets e consultas

Um **QuerySet** representa uma coleção de objetos do banco. É como você *lê*
dados no Django. A característica mais importante: **QuerySets são preguiçosos**
(lazy) — eles não tocam no banco até você realmente precisar dos dados.

!!! quote "A grande sacada"
    Você monta a consulta encadeando filtros. Nada é executado. Só quando você
    **itera**, faz `list()`, `len()`, ou acessa um item, o Django dispara **uma**
    query SQL otimizada.

## O gerenciador `.objects`

Todo modelo tem um **manager** em `.objects`, a porta de entrada para consultas:

```python
Post.objects.all()                    # todos os posts
Post.objects.filter(status="published")  # filtrados
Post.objects.get(slug="ola-mundo")    # um único objeto (ou erro)
Post.objects.exclude(status="draft")  # o complemento de filter
Post.objects.count()                  # SELECT COUNT(*)
```

!!! warning "`.get()` pode levantar exceção"
    - `.get()` retorna **um** objeto. Se não achar, levanta `DoesNotExist`; se
      achar vários, `MultipleObjectsReturned`.
    - Para "pode não existir", use `.filter(...).first()` (retorna `None`) ou o
      atalho `get_object_or_404(...)` nas views.

## Encadeamento e preguiça

Filtros retornam **outro QuerySet**, então você encadeia à vontade:

```python
recentes = (
    Post.objects
    .filter(status="published")
    .exclude(author__display_name="Spam")
    .order_by("-published_at")
)
# Até aqui: NENHUMA query foi executada.

for post in recentes:  # <- AQUI o banco é consultado, uma vez
    print(post.title)
```

## Consultando através de relações

O ORM navega relações com o **duplo underscore** `__`:

```python
# posts cujo autor tem esse nome
Post.objects.filter(author__display_name="Ana")

# posts que têm a tag de slug "django"
Post.objects.filter(tags__slug="django")

# comentários aprovados de um post específico
Comment.objects.filter(post__slug="ola-mundo", is_approved=True)
```

## Custom QuerySet: consultas reutilizáveis e tipadas

Repetir `filter(status="published")` em todo lugar é frágil. Encapsulamos isso
num **QuerySet customizado**, com métodos nomeados e tipados:

```python
class PostQuerySet(models.QuerySet["Post"]):
    """Custom queryset exposing reusable, chainable filters."""

    def published(self) -> "PostQuerySet":
        """Return only posts whose status is published."""
        return self.filter(status=Post.Status.PUBLISHED)

    def by_tag(self, slug: str) -> "PostQuerySet":
        """Return published posts carrying the tag identified by ``slug``."""
        return self.published().filter(tags__slug=slug)


class Post(models.Model):
    # ... campos ...
    objects: PostQuerySet = PostQuerySet.as_manager()
```

Agora o código de leitura fica expressivo e à prova de erro de digitação:

```python
Post.objects.published()            # em vez de filter(status="published")
Post.objects.by_tag("django")       # published + filtro por tag
Post.objects.published().count()    # ainda encadeável!
```

!!! tip "Por que isso é OO de verdade"
    A regra "o que significa *publicado*" mora em **um** lugar. Se amanhã
    "publicado" também exigir `published_at <= agora`, você muda só o método
    `published()`. Nada quebra no resto do código.

## O problema N+1 e como evitar

Este é **o** erro de performance mais comum em Django. Veja:

```python
for post in Post.objects.all():   # 1 query
    print(post.author.display_name)  # +1 query POR post!  😱
```

Se há 100 posts, são **101 queries**. A solução:

=== "`select_related` (FK / OneToOne)"

    ```python
    # Um JOIN: traz o autor junto, em UMA query
    for post in Post.objects.select_related("author"):
        print(post.author.display_name)
    ```

=== "`prefetch_related` (ManyToMany / reverso)"

    ```python
    # Duas queries no total (posts + tags), casadas em memória
    for post in Post.objects.prefetch_related("tags"):
        print([t.name for t in post.tags.all()])
    ```

!!! danger "Regra de ouro"
    Sempre que iterar objetos e acessar uma **FK/OneToOne**, use
    `select_related`. Para **ManyToMany/reverso**, use `prefetch_related`. É por
    isso que nossas views fazem `Post.objects.published().select_related("author")`.

## Criar, atualizar, apagar

```python
# criar
post = Post.objects.create(title="Olá", body="...", author=autor)

# atualizar um objeto
post.title = "Novo título"
post.save()

# atualizar em massa (um único UPDATE, sem carregar objetos)
Post.objects.filter(status="draft").update(status="published")

# apagar
post.delete()
```

!!! quote "📖 Na documentação oficial"
    - [Making queries](https://docs.djangoproject.com/en/stable/topics/db/queries/)

## Recapitulando

- QuerySets são **preguiçosos**: só batem no banco quando os dados são usados.
- `.objects` é o manager; `filter`/`exclude`/`get`/`order_by` são o básico.
- Navegue relações com `campo__subcampo`.
- Encapsule filtros num **QuerySet customizado** tipado (`published()`, `by_tag()`).
- Fuja do **N+1** com `select_related` (FK) e `prefetch_related` (M2M).

Agora sabemos ler dados com eficiência. Bora usar isso nas telas — com as
**[Views baseadas em classe](class-based-views.md)**.
