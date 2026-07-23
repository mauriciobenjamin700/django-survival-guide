# Relações a fundo

Você já viu os três tipos de relação nos [modelos](models.md). Agora vamos
**usá-las de verdade**: navegar de um lado para o outro, adicionar e remover, e
fazer isso sem estourar o banco em mil consultas.

!!! quote "A ideia"
    Relação é uma **ponte** entre dois modelos. O Django deixa você atravessar a
    ponte nos dois sentidos: do post para o autor (`post.author`) e do autor para
    os posts (`author.posts`). O segredo é saber o nome de cada ponta.

## Os dois lados de cada ponte

Toda relação tem um lado **direto** (onde você declarou o campo) e um lado
**reverso** (o outro modelo). O `related_name` batiza o lado reverso.

```python
class Post(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="posts")
    tags = models.ManyToManyField(Tag, related_name="posts")
```

| Da onde | Para onde | Como |
| --- | --- | --- |
| Post → Author | um autor | `post.author` |
| Author → Posts | vários posts | `author.posts.all()` |
| Post → Tags | várias tags | `post.tags.all()` |
| Tag → Posts | vários posts | `tag.posts.all()` |

!!! tip "Sem `related_name`, o Django inventa um"
    O padrão do lado reverso é `<modelo>_set` (ex.: `author.post_set`). Definir
    `related_name="posts"` deixa `author.posts` — bem mais legível. Sempre nomeie.

## ForeignKey (muitos-para-um)

```python
autor = Author.objects.get(display_name="Ana")

# lado reverso: um manager, com toda a API de queryset
autor.posts.all()
autor.posts.filter(status="published")
autor.posts.count()
autor.posts.create(title="Novo", body="...")   # já cria com author=autor
```

!!! info "O lado reverso é um *manager*, não uma lista"
    `author.posts` não é uma lista pronta — é um manager. Por isso você encadeia
    `.filter()`, `.count()`, `.create()` nele, e nada é buscado até você usar.

## OneToOne (um-para-um)

```python
user.author_profile          # o Author daquele usuário
author.user                  # o User daquele autor
```

!!! warning "`RelatedObjectDoesNotExist` no um-para-um"
    Se o `User` ainda não tem `Author`, acessar `user.author_profile` **levanta
    exceção** (não devolve `None`). Proteja com `hasattr(user, "author_profile")`
    ou trate a exceção.

## ManyToMany (muitos-para-muitos)

O manager M2M tem métodos para montar a relação:

```python
post = Post.objects.get(slug="ola-mundo")
django = Tag.objects.get(slug="django")

post.tags.add(django)          # adiciona (idempotente)
post.tags.remove(django)       # remove
post.tags.set([django, orm])   # substitui o conjunto inteiro
post.tags.clear()              # remove todas
post.tags.all()                # lista
```

| Método | Faz |
| --- | --- |
| `.add(obj, ...)` | Adiciona (não duplica) |
| `.remove(obj, ...)` | Remove |
| `.set([...])` | Troca o conjunto todo |
| `.clear()` | Esvazia |

### M2M com dados extras: `through`

E se a relação em si tiver atributos (ex.: *quando* a tag foi aplicada)? Use um
modelo intermediário explícito:

```python
class Tagging(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)


class Post(models.Model):
    tags = models.ManyToManyField(Tag, through="Tagging", related_name="posts")
```

!!! warning "Com `through`, use o modelo intermediário para criar"
    Quando há `through`, os atalhos `.add()`/`.set()` ficam restritos — você cria
    a ligação criando um `Tagging` (que carrega os campos extras).

## Consultando através da ponte

O duplo underscore `__` atravessa relações em filtros:

```python
# posts do autor "Ana"
Post.objects.filter(author__display_name="Ana")

# posts com a tag de slug "django"
Post.objects.filter(tags__slug="django")

# autores que têm pelo menos um post publicado
Author.objects.filter(posts__status="published").distinct()
```

!!! tip "Cuidado com duplicados ao filtrar por M2M/reverso"
    Filtrar por uma relação de "muitos" pode repetir o objeto principal (um autor
    aparece uma vez por post que casa). Use `.distinct()` para colapsar.

## Evitando o N+1 (o ponto que mais dói)

```python
# ❌ N+1: uma query pela lista + uma por autor a cada post
for post in Post.objects.all():
    print(post.author.display_name)

# ✅ FK/OneToOne: select_related (um JOIN)
for post in Post.objects.select_related("author"):
    print(post.author.display_name)

# ✅ M2M/reverso: prefetch_related (buscas casadas)
for post in Post.objects.prefetch_related("tags"):
    print([t.name for t in post.tags.all()])
```

!!! danger "A regra de ouro das relações"
    Vai **iterar** e acessar uma relação? **FK/OneToOne → `select_related`**;
    **M2M/reverso → `prefetch_related`**. Sem isso, uma lista de 100 itens vira
    101 consultas.

## Recapitulando

- Toda relação tem lado direto e reverso; `related_name` batiza o reverso
  (`author.posts`).
- O lado reverso e o M2M são **managers** — encadeie `.filter()`, `.create()`,
  etc.
- M2M: `add`/`remove`/`set`/`clear`; com dados extras, use `through`.
- OneToOne reverso ausente **levanta exceção** — proteja com `hasattr`.
- Atravesse com `__` (use `.distinct()` em M2M); fuja do N+1 com
  `select_related`/`prefetch_related`.

A lista de posts pode crescer muito. Bora dividir em páginas: a
**[paginação](pagination.md)**.
