# Django Channels

Django's normal cycle is: a request comes in, a response goes out, done. That doesn't
work for **real time** — chat, live notifications, a scoreboard that updates
on its own. **Channels** extends Django to **WebSockets** and persistent
connections, over **ASGI**.

!!! quote "Think like a child 🧒"
    Normal HTTP is exchanging **letters**: you send one, get a reply, and the
    post office closes. A WebSocket is an open **phone line**: both sides
    talk whenever they want, all the time, without hanging up. Channels gives that phone
    to Django.

## WSGI vs ASGI (why Channels exists)

Think like a child: traditional Django (WSGI) is a door that opens, lets one
person through and closes. ASGI is a revolving door that holds **many**
connections open at the same time — needed to keep phones (WebSockets)
connected.

| | WSGI (default) | ASGI (Channels) |
| --- | --- | --- |
| Model | Request → response | Persistent connections + async |
| Serves | Pages, REST APIs | WebSocket, SSE, long-polling |
| Server | Gunicorn | Uvicorn/Daphne |

## Installation and configuration

```bash
uv add "channels[daphne]" channels-redis
```

```python
# settings.py
INSTALLED_APPS = [
    "daphne",                 # (1)! before staticfiles/admin
    # ...
    "channels",
]

ASGI_APPLICATION = "config.asgi.application"

CHANNEL_LAYERS = {            # (2)!
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [("127.0.0.1", 6379)]},
    }
}
```

1. `daphne` at the top of the apps takes over `runserver` in ASGI mode.
2. The **channel layer** (Redis) is what lets one consumer **send a message to
    another** — the "cable" between connections. Without it, each connection is isolated.

```python
# config/asgi.py
import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django_asgi = get_asgi_application()

from apps.chat.routing import websocket_urlpatterns   # noqa: E402

application = ProtocolTypeRouter({
    "http": django_asgi,                                  # (1)!
    "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
})
```

1. Normal HTTP keeps going through the usual Django; only `websocket` goes to
    Channels.

## What you can do

### A consumer (the "switchboard operator")

Think like a child: the **consumer** is who answers the phone for that connection —
it receives what you say and decides what to reply or pass along.

```python
# apps/chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    """Handle one chat room's websocket connection."""

    async def connect(self) -> None:
        """Called when a client opens the socket."""
        self.room = self.scope["url_route"]["kwargs"]["room"]
        await self.channel_layer.group_add(self.room, self.channel_name)  # (1)!
        await self.accept()

    async def disconnect(self, code: int) -> None:
        """Called when the socket closes."""
        await self.channel_layer.group_discard(self.room, self.channel_name)

    async def receive(self, text_data: str) -> None:
        """Called when the client sends a message."""
        message = json.loads(text_data)["message"]
        await self.channel_layer.group_send(                              # (2)!
            self.room,
            {"type": "chat.message", "message": message},
        )

    async def chat_message(self, event: dict) -> None:
        """Send a group message down to THIS client."""
        await self.send(text_data=json.dumps({"message": event["message"]}))
```

1. **`group_add`** puts this connection into a "room" — everyone in the room receives whatever is
    sent to the group.
2. **`group_send`** sends to everyone in the room; each one triggers `chat_message`.

```python
# apps/chat/routing.py
from django.urls import path
from apps.chat.consumers import ChatConsumer

websocket_urlpatterns = [
    path("ws/chat/<str:room>/", ChatConsumer.as_asgi()),
]
```

### In the browser (the other end of the phone)

```javascript
const socket = new WebSocket(`ws://${location.host}/ws/chat/general/`);

socket.onmessage = (e) => {
  const data = JSON.parse(e.data);
  console.log("received:", data.message);
};

socket.onopen = () => socket.send(JSON.stringify({ message: "hello!" }));
```

### Sending from outside the consumer (e.g. from a view or task)

Think like a child: ringing everyone's phone in the room from somewhere else
in the building.

```python
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

layer = get_channel_layer()
async_to_sync(layer.group_send)("general", {"type": "chat.message", "message": "notice!"})
```

## When to use it (and when SSE is enough)

!!! tip "Use Channels when..."
    You need **two-way** real time: chat, collaborative editing, games,
    online presence. WebSocket is the right tool.

!!! warning "If the flow is server → client only, consider SSE"
    Notifications, a feed that updates, task progress — in those cases the
    client **only receives**. Then **[SSE](sse.md)** is far simpler (no need for
    ASGI/Redis/consumer). Don't use the WebSocket cannon to kill the "receive-only" fly.

!!! danger "Channels changes your architecture"
    ASGI + Daphne/Uvicorn + Redis channel layer + separate processes. It's a jump
    in complexity and deploy. Adopt it when bidirectional real time is a
    **real requirement**, not a "would be nice".

## Recap

- Channels brings Django into **real time** via **WebSocket** over **ASGI**.
- Pieces: `daphne`/Uvicorn (ASGI server), `ASGI_APPLICATION`, the **channel layer**
  (Redis) to connect connections, and **consumers** (async) that answer the socket.
- `group_add`/`group_send` make rooms; `async_to_sync(layer.group_send)` sends from
  outside the consumer.
- WebSocket is **bidirectional**; if the client only receives, prefer [SSE](sse.md).

!!! quote "📖 In the official docs"
    - [Django Channels](https://channels.readthedocs.io/)

For the simpler receive-only real-time path: **[SSE](sse.md)**.
