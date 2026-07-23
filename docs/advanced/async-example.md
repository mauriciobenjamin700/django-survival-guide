# Exemplo assíncrono (blog em async)

O repositório traz um **segundo projeto**, `example_async/`, com o mesmo blog
reescrito em **Django async**. Aqui destrinchamos o que muda em relação ao
[exemplo síncrono](../tutorial/project-setup.md). Leia primeiro
[sync × async](sync-vs-async.md) para o porquê.

!!! quote "Pensa como criança 🧒"
    É o mesmo blog — as mesmas caixas (models), as mesmas telas. Só trocamos o
    garçom síncrono pelo assíncrono: as views viram `async def` e falam com o
    banco pela API `a...`. Nada mais precisa mudar.

## Rodando

```bash
cd example_async
uv run python manage.py migrate
uv run python manage.py seed_blog
uv run uvicorn config.asgi:application --reload      # (1)!
```

1. **Uvicorn** (ASGI), não `runserver`/Gunicorn — é o que faz as views async
    renderem concorrência de verdade.

## O que é idêntico

- **Models** (`Post`, `Author`, `Tag`, `Comment`) — o esquema não muda entre sync
  e async.
- **Templates** — a renderização é a mesma; só entregamos listas já prontas.
- **URLs** — funções async entram no `path()` igual às síncronas.

## O que muda: as views

Comparando o mesmo `post_detail` nos dois estilos:

=== "Síncrono"

    ```python
    from django.shortcuts import get_object_or_404, render

    def post_detail(request, slug):
        post = get_object_or_404(Post.objects.published().select_related("author"), slug=slug)
        comments = post.approved_comments()
        return render(request, "blog/post_detail.html",
                      {"post": post, "comments": comments, "form": CommentForm()})
    ```

=== "Assíncrono"

    ```python
    from django.shortcuts import aget_object_or_404, render

    async def post_detail(request, slug):
        post = await aget_object_or_404(
            Post.objects.published().select_related("author"), slug=slug,
        )
        comments = [c async for c in post.approved_comments()]   # (1)!
        return render(request, "blog/post_detail.html",
                      {"post": post, "comments": comments, "form": CommentForm()})
    ```

1. `async for` + materializar numa lista: o template itera de forma síncrona, então
    resolvemos o banco **antes**.

### A lista

```python
async def post_list(request):
    posts = [
        post
        async for post in Post.objects.published().select_related("author")
    ]
    return render(request, "blog/post_list.html", {"posts": posts})
```

### Escrever no POST

```python
async def comment_create(request, slug):
    post = await aget_object_or_404(Post.objects.published(), slug=slug)
    form = CommentForm(request.POST)          # (1)!
    if form.is_valid():
        await Comment.objects.acreate(post=post, **form.cleaned_data)   # (2)!
    return HttpResponseRedirect(post.get_absolute_url())
```

1. A validação do form é síncrona (só CPU) — pode chamar `is_valid()` direto.
2. A escrita usa `acreate` (async). Se usássemos `form.save()` (síncrono, toca o
    banco) daria `SynchronousOnlyOperation` — por isso `acreate` com
    `cleaned_data`.

!!! danger "Materialize antes do template; pré-carregue relações"
    Dois cuidados que evitam o `SynchronousOnlyOperation`:

    - Transforme o queryset em **lista** com `async for` antes de passar ao
      template (o template não sabe fazer `await`).
    - Use `select_related`/`prefetch_related` para o template não disparar uma
      query síncrona ao acessar `post.author`.

## `render` síncrono numa view async?

Sim — nesta versão do Django não há `arender`, e o `render` **não** toca o banco
(os dados já vieram materializados), então chamá-lo direto é seguro. Se um dia
precisar de rendering assíncrono de verdade, use `sync_to_async(render)(...)`.

## O que NÃO virou async

- **Management commands** (`seed_blog`) — rodam sync; usam o ORM normal.
- **Admin** — o admin do Django é síncrono.
- **Forms** — a validação é CPU; só a persistência foi para o `acreate`.

Isso é normal: async é sobre **servir requisições** com concorrência, não sobre
tornar tudo assíncrono.

## Quando este blog se beneficia de async

Honestamente? Um blog CRUD **não** ganha muito com async — ele é o exemplo
didático. O ganho apareceria se a view, por exemplo, chamasse **várias APIs
externas** em paralelo (`asyncio.gather`) ou mantivesse conexões longas
([SSE](../libs/sse.md)/[WebSocket](../libs/channels.md)). O valor aqui é
**aprender o padrão** com algo familiar.

## Recapitulando

- `example_async/` é o mesmo blog em Django async: models/templates/URLs iguais,
  **views `async def`** com ORM `a...` (`aget_object_or_404`, `async for`,
  `acreate`).
- Materialize listas e pré-carregue relações antes do template; `render` sync é
  ok porque não toca o banco.
- Sirva com **Uvicorn (ASGI)**; commands/admin/forms seguem síncronos.
- Para um CRUD, async é didático; o ganho real é com I/O concorrente e conexões
  longas.

!!! quote "📖 Na documentação oficial"
    - [Async views (Django)](https://docs.djangoproject.com/en/stable/topics/async/)
    - [ASGI deployment (Django)](https://docs.djangoproject.com/en/stable/howto/deployment/asgi/)

Conceito e prática cobertos. Volte a [sync × async](sync-vs-async.md) ou ao
[mapa da referência](../referencia/index.md).
