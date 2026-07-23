# QuerySets and queries

A **QuerySet** represents a collection of objects from the database. It's how you *read*
data in Django. The most important characteristic: **QuerySets are lazy** — they don't touch the database until you actually need the data.

!!! quote "The big insight"
    You build the query by chaining filters. Nothing is executed. Only when you
    **iterate**, call `list()`, `len()`, or access an item does Django fire **one**
    optimized SQL query.

## The `.objects` manager

Every model has a **manager** at `.objects`, the entry point for queries:

```python
Post.objects.all()                    # todos os posts
Post.objects.filter(status="published")  # filtrados
Post.objects.get(slug="ola-mundo")    # um único objeto (ou erro)
Post.objects.exclude(status="draft")  # o complemento de filter
Post.objects.count()                  # SELECT COUNT(*)
```

!!! warning "`.get()` can raise an exception"
    - `.get()` returns **one** object. If it finds none, it raises `DoesNotExist`; if
      it finds several, `MultipleObjectsReturned`.
    - For "may not exist", use `.filter(...).first()` (returns `None`) or the
      `get_object_or_404(...)` shortcut in views.

## Chaining and laziness

Filters return **another QuerySet**, so you can chain freely:

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

## Querying through relationships

The ORM navigates relationships with the **double underscore** `__`:

```python
# posts cujo autor tem esse nome
Post.objects.filter(author__display_name="Ana")

# posts que têm a tag de slug "django"
Post.objects.filter(tags__slug="django")

# comentários aprovados de um post específico
Comment.objects.filter(post__slug="ola-mundo", is_approved=True)
```

## Custom QuerySet: reusable, typed queries

Repeating `filter(status="published")` everywhere is fragile. We encapsulate it
in a **custom QuerySet**, with named and typed methods:

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

Now the reading code becomes expressive and typo-proof:

```python
Post.objects.published()            # em vez de filter(status="published")
Post.objects.by_tag("django")       # published + filtro por tag
Post.objects.published().count()    # ainda encadeável!
```

!!! tip "Why this is real OO"
    The rule "what *published* means" lives in **one** place. If tomorrow
    "published" also requires `published_at <= now`, you change only the
    `published()` method. Nothing else in the code breaks.

## The N+1 problem and how to avoid it

This is **the** most common performance mistake in Django. Look:

```python
for post in Post.objects.all():   # 1 query
    print(post.author.display_name)  # +1 query POR post!  😱
```

If there are 100 posts, that's **101 queries**. The solution:

=== "`select_related` (FK / OneToOne)"

    ```python
    # Um JOIN: traz o autor junto, em UMA query
    for post in Post.objects.select_related("author"):
        print(post.author.display_name)
    ```

=== "`prefetch_related` (ManyToMany / reverse)"

    ```python
    # Duas queries no total (posts + tags), casadas em memória
    for post in Post.objects.prefetch_related("tags"):
        print([t.name for t in post.tags.all()])
    ```

!!! danger "Golden rule"
    Whenever you iterate objects and access an **FK/OneToOne**, use
    `select_related`. For **ManyToMany/reverse**, use `prefetch_related`. That's why
    our views do `Post.objects.published().select_related("author")`.

## Create, update, delete

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

!!! quote "📖 In the official docs"
    - [Making queries](https://docs.djangoproject.com/en/stable/topics/db/queries/)

## Recap

- QuerySets are **lazy**: they only hit the database when the data is used.
- `.objects` is the manager; `filter`/`exclude`/`get`/`order_by` are the basics.
- Navigate relationships with `field__subfield`.
- Encapsulate filters in a typed **custom QuerySet** (`published()`, `by_tag()`).
- Escape the **N+1** with `select_related` (FK) and `prefetch_related` (M2M).

Now we know how to read data efficiently. Let's put it to use on the screens — with the
**[Class-based views](class-based-views.md)**.
