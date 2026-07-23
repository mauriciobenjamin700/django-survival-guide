# Django sync × async

O Django nasceu **síncrono**: uma requisição ocupa um worker do começo ao fim.
Desde a versão 3+ ele também fala **async** — views `async def`, ORM assíncrono,
ASGI. Esta página explica **quando** async ajuda (e quando não) antes do
[exemplo prático](async-example.md).

!!! quote "Pensa como criança 🧒"
    Imagine um garçom (o worker). No modo **síncrono**, ele leva seu pedido à
    cozinha e **fica parado** esperando o prato ficar pronto, sem atender mais
    ninguém. No modo **assíncrono**, ele anota seu pedido, vai atender outras
    mesas, e volta quando o prato está pronto. Mesmo garçom, muito mais mesas
    atendidas — **se** houver espera (I/O) para aproveitar.

## O que muda: WSGI × ASGI

| | Síncrono (WSGI) | Assíncrono (ASGI) |
| --- | --- | --- |
| Servidor | Gunicorn | Uvicorn / Daphne |
| View | `def` | `async def` |
| Concorrência | 1 requisição por worker/thread | muitas por worker (no `await`) |
| Ganho real | — | Quando a view **espera I/O** |

!!! info "Async não é 'mais rápido' — é 'mais concorrente'"
    Uma view async **não** processa CPU mais rápido. O ganho aparece quando ela
    **espera** algo (banco, uma API externa, um arquivo): enquanto espera, o
    worker atende outra requisição. Se a view só faz cálculo (CPU), async não
    ajuda — pode até atrapalhar.

## Quando usar async

!!! tip "Async brilha quando..."
    - A view faz **muitas chamadas de I/O** que podem ir em paralelo (ex.: chamar
      3 APIs externas ao mesmo tempo).
    - Você mantém **conexões longas** (SSE, WebSocket via [Channels](../libs/channels.md)).
    - Há **muita espera** por requisição e você quer aguentar mais conexões
      simultâneas com o mesmo hardware.

!!! warning "Fique no síncrono quando..."
    - A app é o CRUD comum (a maioria!) — o síncrono é mais simples e igualmente
      rápido.
    - O trabalho é **CPU-bound** (processar imagem, cálculo pesado) → isso vai
      para uma [tarefa Celery](../libs/celery.md), não para async.
    - Sua stack (drivers, libs) ainda é sync — misturar mal dá dor de cabeça.

## O ORM assíncrono

Toda operação de banco ganhou uma versão com prefixo **`a`**, e a iteração usa
**`async for`**:

| Síncrono | Assíncrono |
| --- | --- |
| `for p in qs:` | `async for p in qs:` |
| `Model.objects.get(...)` | `await Model.objects.aget(...)` |
| `.first()` / `.count()` / `.exists()` | `await .afirst()` / `.acount()` / `.aexists()` |
| `Model.objects.create(...)` | `await Model.objects.acreate(...)` |
| `obj.save()` / `obj.delete()` | `await obj.asave()` / `await obj.adelete()` |
| `get_object_or_404(...)` | `await aget_object_or_404(...)` |

```python
# materialize o queryset numa lista antes do template
posts = [post async for post in Post.objects.published()]

# um objeto
post = await aget_object_or_404(Post.objects.published(), slug=slug)

# escrever
await Comment.objects.acreate(post=post, author_name="Ana", body="oi")
```

!!! danger "O erro nº 1: `SynchronousOnlyOperation`"
    Chamar o ORM **síncrono** dentro de uma view async levanta
    `SynchronousOnlyOperation`. Ex.: `post.author` dispara uma query síncrona se o
    autor não foi pré-carregado. Soluções:

    - Use a **API async** (`aget`, `async for`, `acreate`).
    - **Pré-carregue** relações com `select_related`/`prefetch_related` e
      materialize a lista **antes** de renderizar o template.
    - Para código sync inevitável que toca o banco, envolva em
      `sync_to_async(...)`.

## Misturar os dois mundos

Pensa como criança: `sync_to_async` é o **tradutor** que deixa o garçom async
falar com a cozinha síncrona, e `async_to_sync` faz o contrário.

```python
from asgiref.sync import sync_to_async, async_to_sync

# chamar código SÍNCRONO de dentro de uma view async
resultado = await sync_to_async(funcao_sync_que_usa_orm)()

# chamar código ASYNC de dentro de código síncrono (ex.: um comando)
async_to_sync(minha_corotina)()
```

!!! info "Views, middleware e ORM são async; muita coisa ainda é sync"
    O Django deixa você misturar: uma view async pode chamar helpers sync (via
    `sync_to_async`), e o framework adapta middleware sync/async automaticamente.
    Comandos de management, signals e a maior parte de libs de terceiros ainda são
    síncronos — e tudo bem.

## Como servir

```bash
# síncrono
gunicorn config.wsgi:application

# assíncrono (necessário para as views async renderem concorrência de verdade)
uvicorn config.asgi:application
```

!!! warning "View async sob WSGI não ganha nada"
    Se você servir views async com Gunicorn/WSGI, o Django as roda numa camada de
    compatibilidade e o ganho de concorrência **some**. Async pede um servidor
    **ASGI** (Uvicorn/Daphne). Ver [deploy](../referencia/deploy.md).

## Recapitulando

- Async = mais **concorrência** sob I/O, não mais velocidade de CPU. A maioria
  dos apps (CRUD) vive feliz no síncrono.
- WSGI (`def`, Gunicorn) × ASGI (`async def`, Uvicorn); async precisa de servidor
  ASGI para valer.
- ORM async: prefixo `a` (`aget`/`acreate`/`asave`) e `async for`; materialize
  listas e pré-carregue relações antes do template.
- Cuidado com `SynchronousOnlyOperation`; use `sync_to_async`/`async_to_sync`
  para cruzar os mundos.
- CPU-bound → Celery, não async.

!!! quote "📖 Na documentação oficial"
    - [Async support (Django)](https://docs.djangoproject.com/en/stable/topics/async/)
    - [Asynchronous ORM queries](https://docs.djangoproject.com/en/stable/topics/db/queries/#asynchronous-queries)

Agora veja o blog **inteiro reescrito em async**: o
**[exemplo assíncrono](async-example.md)**.
