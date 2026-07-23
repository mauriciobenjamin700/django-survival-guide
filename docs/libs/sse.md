# SSE — Server-Sent Events

Quer o servidor **empurrar** atualizações para o navegador (notificações, um feed
ao vivo, progresso de uma tarefa) sem o cliente ficar perguntando toda hora? Se o
fluxo é **só do servidor para o cliente**, o **SSE** é o caminho mais simples — e
o Django faz nativamente, sem Channels, sem Redis.

!!! quote "Pensa como criança 🧒"
    WebSocket é um telefone (os dois falam). SSE é um **rádio**: a estação (o
    servidor) transmite e você (o navegador) só escuta. Para "me avise quando algo
    acontecer", ouvir o rádio basta — e é muito mais simples que instalar um
    telefone.

## SSE × WebSocket × polling

| Técnica | Direção | Complexidade | Bom para |
| --- | --- | --- | --- |
| **Polling** | Cliente pergunta toda hora | Baixa (mas desperdiça) | Nada em tempo real de verdade |
| **SSE** | Servidor → cliente (uma via) | **Baixa** (HTTP puro) | Notificações, feeds, progresso |
| **WebSocket** | Ambos (duas vias) | Alta (ASGI/Channels) | Chat, jogos, colaboração |

!!! tip "Comece pelo SSE quando só o servidor fala"
    90% dos "quero tempo real" são só-recebimento. SSE resolve com uma view
    comum, reconecta sozinho e passa por qualquer proxy HTTP. Só suba para
    [WebSocket](channels.md) quando precisar de duas vias.

## Como funciona: uma resposta que não fecha

O SSE é uma resposta HTTP com `Content-Type: text/event-stream` que **fica
aberta**, mandando linhas no formato `data: ...` conforme os eventos surgem.

### View com `StreamingHttpResponse` (async)

```python
# apps/notify/views.py
import asyncio
import json
from collections.abc import AsyncIterator

from django.http import StreamingHttpResponse


async def event_stream() -> AsyncIterator[str]:
    """Yield SSE events forever, one per second."""
    n = 0
    while True:
        n += 1
        payload = json.dumps({"count": n})
        yield f"data: {payload}\n\n"      # (1)!
        await asyncio.sleep(1)


async def sse(request) -> StreamingHttpResponse:
    """Serve the event stream to the browser."""
    response = StreamingHttpResponse(
        event_stream(),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"    # (2)!
    response["X-Accel-Buffering"] = "no"      # (3)!
    return response
```

1. O formato SSE é literal: `data: <conteúdo>` seguido de **duas** quebras de
    linha (`\n\n`) para fechar o evento. Faltou o `\n\n` → o navegador não
    dispara.
2. Sem cache — cada evento é único.
3. Desliga o buffering do Nginx, senão os eventos ficam presos até acumular.

```python
# urls.py
path("sse/", views.sse, name="sse"),
```

### No navegador: `EventSource`

Pensa como criança: ligar o rádio numa estação. O `EventSource` já **reconecta
sozinho** se a conexão cair.

```javascript
const source = new EventSource("/sse/");

source.onmessage = (e) => {
  const data = JSON.parse(e.data);
  console.log("chegou:", data.count);
};

source.onerror = () => console.log("caiu — o navegador vai reconectar sozinho");
```

## Possibilidades

### Eventos nomeados

Você pode rotular eventos e o cliente escuta cada tipo:

```python
yield f"event: notification\ndata: {payload}\n\n"
yield f"event: heartbeat\ndata: {{}}\n\n"
```

```javascript
source.addEventListener("notification", (e) => { /* ... */ });
```

### Reconexão e `id`

Mande um `id:` em cada evento; se cair, o navegador reenvia o último id no
cabeçalho `Last-Event-ID`, e você retoma de onde parou.

```python
yield f"id: {n}\ndata: {payload}\n\n"
```

### Rodando de verdade

!!! warning "SSE precisa de um servidor async e worker que não bufferize"
    A conexão fica aberta. Sirva a view async com **Uvicorn/Daphne** (ASGI) — o
    `runserver` funciona para testar. No Nginx, desligue o buffer para essa rota
    (`proxy_buffering off;`), senão os eventos chegam em bloco. E cada conexão
    ocupa um worker enquanto estiver aberta — dimensione os workers.

!!! danger "Feche o loop quando o cliente sumir"
    Um `while True` que ninguém escuta vaza recursos. Em produção, limite o tempo
    de vida do stream, mande **heartbeats** para detectar queda, e trate o
    disconnect. Para muitos clientes simultâneos, um broker (Redis pub/sub)
    alimentando os streams escala melhor que loops isolados.

## Recapitulando

- SSE = servidor **empurra** eventos numa via só, sobre HTTP comum — o jeito
  simples de tempo real quando o cliente só recebe.
- No Django: uma view async que devolve `StreamingHttpResponse` com
  `text/event-stream`, cada evento no formato `data: ...\n\n`.
- No navegador: `EventSource` (reconecta sozinho); eventos nomeados via
  `event:` + `addEventListener`.
- Sirva com ASGI (Uvicorn/Daphne), desligue buffering no proxy, mande heartbeats
  e feche streams órfãos.
- Precisa de duas vias? Aí sim [WebSocket/Channels](channels.md).

!!! quote "📖 Na documentação oficial"
    - [StreamingHttpResponse (Django)](https://docs.djangoproject.com/en/stable/ref/request-response/#streaminghttpresponse-objects)
    - [Server-sent events (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

Empurrar para uma aba aberta é ótimo. E avisar o usuário mesmo com o site
fechado? **[Web Push](webpush.md)**.
