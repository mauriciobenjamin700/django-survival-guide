# Django Channels

O ciclo normal do Django é: chega uma requisição, sai uma resposta, fim. Isso não
serve para **tempo real** — chat, notificações ao vivo, um placar que atualiza
sozinho. O **Channels** estende o Django para **WebSockets** e conexões
persistentes, sobre **ASGI**.

!!! quote "Pensa como criança 🧒"
    O HTTP normal é trocar **cartas**: você manda uma, recebe uma resposta, e o
    correio fecha. O WebSocket é uma **linha telefônica** aberta: os dois lados
    falam quando quiserem, o tempo todo, sem desligar. O Channels dá esse telefone
    ao Django.

## WSGI × ASGI (por que o Channels existe)

Pensa como criança: o Django tradicional (WSGI) é uma porta que abre, deixa uma
pessoa passar e fecha. O ASGI é uma porta giratória que segura **várias**
conexões abertas ao mesmo tempo — necessário para manter telefones (WebSockets)
ligados.

| | WSGI (padrão) | ASGI (Channels) |
| --- | --- | --- |
| Modelo | Request → response | Conexões persistentes + async |
| Serve | Páginas, APIs REST | WebSocket, SSE, long-polling |
| Servidor | Gunicorn | Uvicorn/Daphne |

## Instalação e configuração

```bash
uv add "channels[daphne]" channels-redis
```

```python
# settings.py
INSTALLED_APPS = [
    "daphne",                 # (1)! antes de staticfiles/admin
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

1. `daphne` no topo dos apps assume o `runserver` em modo ASGI.
2. O **channel layer** (Redis) é o que permite um consumer **enviar mensagem para
    outro** — o "cabo" entre conexões. Sem ele, cada conexão fica isolada.

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

1. HTTP normal continua indo pelo Django de sempre; só o `websocket` vai para o
    Channels.

## Possibilidades

### Um consumer (o "telefonista")

Pensa como criança: o **consumer** é quem atende o telefone daquela conexão —
recebe o que você fala e decide o que responder ou repassar.

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

1. **`group_add`** põe esta conexão numa "sala" — todos na sala recebem o que for
    enviado ao grupo.
2. **`group_send`** manda para todos na sala; cada um dispara `chat_message`.

```python
# apps/chat/routing.py
from django.urls import path
from apps.chat.consumers import ChatConsumer

websocket_urlpatterns = [
    path("ws/chat/<str:room>/", ChatConsumer.as_asgi()),
]
```

### No navegador (o outro lado do telefone)

```javascript
const socket = new WebSocket(`ws://${location.host}/ws/chat/geral/`);

socket.onmessage = (e) => {
  const data = JSON.parse(e.data);
  console.log("recebeu:", data.message);
};

socket.onopen = () => socket.send(JSON.stringify({ message: "olá!" }));
```

### Enviar de fora do consumer (ex.: de uma view ou tarefa)

Pensa como criança: tocar o telefone de todo mundo da sala a partir de outro
lugar do prédio.

```python
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

layer = get_channel_layer()
async_to_sync(layer.group_send)("geral", {"type": "chat.message", "message": "aviso!"})
```

## Quando usar (e quando SSE já basta)

!!! tip "Use Channels quando..."
    Você precisa de **duas vias** em tempo real: chat, edição colaborativa, jogos,
    presença online. WebSocket é a ferramenta certa.

!!! warning "Se o fluxo é só do servidor → cliente, considere SSE"
    Notificações, um feed que atualiza, progresso de tarefa — nesses casos o
    cliente **só recebe**. Aí **[SSE](sse.md)** é bem mais simples (não precisa de
    ASGI/Redis/consumer). Não use o canhão do WebSocket para matar a mosca do
    "só-receber".

!!! danger "Channels muda sua arquitetura"
    ASGI + Daphne/Uvicorn + Redis channel layer + processos separados. É um salto
    de complexidade e de deploy. Adote quando o tempo real bidirecional for
    **requisito real**, não "seria legal".

## Recapitulando

- Channels leva o Django ao **tempo real** via **WebSocket** sobre **ASGI**.
- Peças: `daphne`/Uvicorn (servidor ASGI), `ASGI_APPLICATION`, **channel layer**
  (Redis) para conectar conexões, e **consumers** (async) que atendem o socket.
- `group_add`/`group_send` fazem salas; `async_to_sync(layer.group_send)` envia de
  fora do consumer.
- WebSocket é **bidirecional**; se o cliente só recebe, prefira [SSE](sse.md).

!!! quote "📖 Na documentação oficial"
    - [Django Channels](https://channels.readthedocs.io/)

Para o caminho mais simples de tempo real só-recebimento: **[SSE](sse.md)**.
