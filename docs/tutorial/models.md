# Modelos e o ORM

Um **modelo** é uma classe Python que representa uma tabela do banco. Cada
atributo é uma coluna. O **ORM** (Object-Relational Mapper) traduz operações em
objetos Python para SQL — você trabalha com objetos, o Django escreve o SQL.

!!! quote "A ideia central"
    Você descreve os dados **uma vez**, como uma classe. O Django gera as
    tabelas, valida os dados e te dá uma API para consultar — sem você escrever
    SQL na mão.

## Nosso primeiro modelo: `Tag`

Vamos do mais simples ao mais complexo. Uma `Tag` é só um rótulo:

```python
from django.db import models
from django.utils.text import slugify


class Tag(models.Model):
    """A free-form label used to group related posts."""

    name = models.CharField(max_length=40, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        """Return the tag name."""
        return self.name

    def save(self, *args: object, **kwargs: object) -> None:
        """Populate ``slug`` from ``name`` on first save when left blank."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
```

Vamos por partes:

- **`models.Model`** — toda classe de modelo herda dela. É o que dá acesso ao
  ORM (`.objects`, `.save()`, etc.).
- **`CharField` / `SlugField`** — tipos de coluna. `max_length` é obrigatório em
  texto curto; `unique=True` cria uma restrição de unicidade no banco.
- **`blank=True`** — permite o campo vazio *nos formulários* (validação).
- **`class Meta`** — metadados do modelo. `ordering` define a ordem padrão das
  consultas.
- **`__str__`** — como o objeto aparece no admin e no shell. Sempre defina.
- **`save()` sobrescrito** — geramos o `slug` a partir do `name` na primeira vez.
  Chamamos `super().save(...)` para o Django fazer o trabalho de fato.

!!! warning "`blank` vs `null`"
    - **`blank`** é sobre **validação de formulário** (o campo pode ficar vazio).
    - **`null`** é sobre o **banco** (a coluna aceita `NULL`).

    Para campos de texto, prefira `blank=True` e **não** use `null=True` — assim
    "vazio" é sempre `""`, nunca `None`, evitando dois jeitos de dizer "nada".

## Relacionamentos

Aqui mora o poder do ORM. Nosso blog tem três tipos de relação:

=== "Um-para-um (`Author` ↔ `User`)"

    ```python
    from django.conf import settings


    class Author(models.Model):
        """A public author profile attached one-to-one to an auth user."""

        user = models.OneToOneField(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name="author_profile",
        )
        display_name = models.CharField(max_length=80)
        bio = models.TextField(blank=True)
        website = models.URLField(blank=True)
    ```

    Separamos o perfil público (`Author`) do usuário de autenticação (`User`).
    Um usuário tem **um** perfil. Acessamos com `user.author_profile`.

=== "Muitos-para-um (`Post` → `Author`)"

    ```python
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    ```

    Cada post tem **um** autor; um autor tem **vários** posts. O
    `related_name="posts"` cria o caminho reverso: `author.posts.all()`.

=== "Muitos-para-muitos (`Post` ↔ `Tag`)"

    ```python
    tags = models.ManyToManyField(Tag, related_name="posts", blank=True)
    ```

    Um post tem várias tags; uma tag marca vários posts. O Django cria a tabela
    intermediária sozinho.

!!! danger "Sempre defina `on_delete`"
    Em `ForeignKey` e `OneToOneField`, `on_delete` é **obrigatório**. Ele diz o
    que fazer quando o objeto referenciado é apagado:

    - `CASCADE` — apaga também os que dependem dele (apagou o autor, somem os posts).
    - `PROTECT` — impede o apagamento enquanto houver dependentes.
    - `SET_NULL` — zera a referência (exige `null=True`).

## O modelo central: `Post`

Reunindo tudo, mais um **enum de status** e propriedades:

```python
from django.urls import reverse
from django.utils import timezone


class Post(models.Model):
    """A blog post authored by an Author and labelled with tags."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="posts")
    body = models.TextField()
    tags = models.ManyToManyField(Tag, related_name="posts", blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [models.Index(fields=["-published_at"])]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        """Return the canonical URL of the post detail page."""
        return reverse("blog:post-detail", kwargs={"slug": self.slug})

    @property
    def is_published(self) -> bool:
        return self.status == self.Status.PUBLISHED
```

Destaques:

- **`TextChoices`** — a forma moderna e tipada de definir opções. `Status.DRAFT`
  vale `"draft"` e exibe `"Draft"`. Sem constantes soltas nem strings mágicas.
- **`auto_now_add`** vs **`auto_now`** — o primeiro grava a data só na criação; o
  segundo atualiza a cada save.
- **`get_absolute_url`** — retorna a URL do objeto. O admin e os templates usam
  isso; nunca escrevemos a URL "na mão".
- **`indexes`** — um índice no banco para ordenar por `published_at` rápido.
- **`@property is_published`** — lógica de domínio junto do modelo, tipada.

!!! tip "Modelo gordo, view magra"
    Regras que dependem só dos dados do próprio objeto (como `is_published`)
    moram no **modelo**. Assim a lógica fica perto dos dados e é reaproveitável
    em views, templates e testes.

!!! quote "📖 Na documentação oficial"
    - [Models](https://docs.djangoproject.com/en/stable/topics/db/models/)

## Recapitulando

- Um **modelo** é uma classe que vira tabela; atributos viram colunas.
- Relacionamentos: `OneToOneField`, `ForeignKey`, `ManyToManyField` — sempre com
  `on_delete` nas FKs.
- `related_name` cria o acesso reverso (`author.posts`).
- `TextChoices` dá enums tipados; `__str__` e `get_absolute_url` são essenciais.
- Coloque regras do próprio objeto no modelo (`@property`, métodos).

Definimos as tabelas em código. Agora precisamos criá-las de verdade no banco —
isso é papel das **[Migrações](migrations.md)**.
