# SSE — Server-Sent Events

Want the server to **push** updates to the browser (notifications, a live feed, the
progress of a task) without the client having to ask all the time? If the
flow is **server to client only**, **SSE** is the simplest path — and
Django does it natively, no Channels, no Redis.

!!! quote "Think like a child 🧒"
    A WebSocket is a phone (both talk). SSE is a **radio**: the station (the
    server) broadcasts and you (the browser) just listen. For "let me know when something
    happens", listening to the radio is enough — and it's much simpler than installing a
    phone.

## SSE vs WebSocket vs polling

| Technique | Direction | Complexity | Good for |
| --- | --- | --- | --- |
| **Polling** | Client asks all the time | Low (but wasteful) | Nothing truly real time |
| **SSE** | Server → client (one way) | **Low** (plain HTTP) | Notifications, feeds, progress |
| **WebSocket** | Both (two ways) | High (ASGI/Channels) | Chat, games, collaboration |

!!! tip "Start with SSE when only the server talks"
    90% of "I want real time" is receive-only. SSE solves it with an ordinary
    view, reconnects on its own and passes through any HTTP proxy. Only step up to
    [WebSocket](channels.md) when you need two ways.

## How it works: a response that doesn't close

SSE is an HTTP response with `Content-Type: text/event-stream` that **stays
open**, sending lines in the `data: ...` format as events come up.

### View with `StreamingHttpResponse` (async)

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

1. The SSE format is literal: `data: <content>` followed by **two** line
    breaks (`\n\n`) to close the event. Missing the `\n\n` → the browser doesn't
    fire.
2. No cache — each event is unique.
3. Turns off Nginx buffering, otherwise events get stuck until they pile up.

```python
# urls.py
path("sse/", views.sse, name="sse"),
```

### In the browser: `EventSource`

Think like a child: turning the radio on to a station. `EventSource` already
**reconnects on its own** if the connection drops.

```javascript
const source = new EventSource("/sse/");

source.onmessage = (e) => {
  const data = JSON.parse(e.data);
  console.log("arrived:", data.count);
};

source.onerror = () => console.log("dropped — the browser will reconnect on its own");
```

## What you can do

### Named events

You can label events and the client listens to each type:

```python
yield f"event: notification\ndata: {payload}\n\n"
yield f"event: heartbeat\ndata: {{}}\n\n"
```

```javascript
source.addEventListener("notification", (e) => { /* ... */ });
```

### Reconnection and `id`

Send an `id:` on each event; if it drops, the browser resends the last id in the
`Last-Event-ID` header, and you resume from where you left off.

```python
yield f"id: {n}\ndata: {payload}\n\n"
```

### Running it for real

!!! warning "SSE needs an async server and a worker that doesn't buffer"
    The connection stays open. Serve the async view with **Uvicorn/Daphne** (ASGI) — the
    `runserver` works for testing. In Nginx, turn off the buffer for that route
    (`proxy_buffering off;`), otherwise events arrive in a block. And each connection
    occupies a worker while it's open — size your workers accordingly.

!!! danger "Close the loop when the client goes away"
    A `while True` that nobody listens to leaks resources. In production, limit the stream's
    lifetime, send **heartbeats** to detect drops, and handle the
    disconnect. For many simultaneous clients, a broker (Redis pub/sub)
    feeding the streams scales better than isolated loops.

## Recap

- SSE = the server **pushes** events one way, over plain HTTP — the simple
  way to do real time when the client only receives.
- In Django: an async view that returns `StreamingHttpResponse` with
  `text/event-stream`, each event in the `data: ...\n\n` format.
- In the browser: `EventSource` (reconnects on its own); named events via
  `event:` + `addEventListener`.
- Serve it with ASGI (Uvicorn/Daphne), turn off proxy buffering, send heartbeats
  and close orphaned streams.
- Need two ways? Then yes, [WebSocket/Channels](channels.md).

!!! quote "📖 In the official docs"
    - [StreamingHttpResponse (Django)](https://docs.djangoproject.com/en/stable/ref/request-response/#streaminghttpresponse-objects)
    - [Server-sent events (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

Pushing to an open tab is great. And notifying the user even with the site
closed? **[Web Push](webpush.md)**.
