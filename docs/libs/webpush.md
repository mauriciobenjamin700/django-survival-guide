# Web Push (notificações)

SSE e WebSocket só entregam enquanto a aba está **aberta**. **Web Push** vai além:
notifica o usuário mesmo com o site **fechado** — como um app de celular. É o que
falta para o Django parecer tão "moderno" quanto um app React/mobile.

!!! quote "Pensa como criança 🧒"
    SSE/WebSocket é falar com alguém que está na sala. Web Push é mandar uma
    **carta que aparece na porta** da pessoa mesmo com a casa vazia — o carteiro
    (o serviço de push do navegador) entrega, e ela vê quando chegar. Funciona
    porque o navegador deixou um **carteiro de plantão** (o service worker).

## As peças (e por que são tantas)

```mermaid
flowchart LR
    U["Navegador<br/>(service worker)"] -->|1. assina, dá a subscription| D["Django"]
    D -->|2. guarda a subscription| DB["Banco"]
    D -->|3. envia push assinado (VAPID)| P["Push service<br/>(Google/Mozilla)"]
    P -->|4. entrega a notificação| U
```

- **Service worker** — um script que o navegador mantém rodando em segundo plano,
  mesmo com a aba fechada. É ele que recebe e mostra a notificação.
- **Subscription** — a "caixa postal" daquele navegador (uma URL + chaves),
  gerada quando o usuário **permite** notificações. Você guarda no banco.
- **VAPID** — um par de chaves (pública/privada) que **assina** os envios, provando
  que é você. O push service exige isso.
- **Push service** — infraestrutura do próprio navegador (Google/Mozilla), não sua.

## Instalação e chaves

```bash
uv add pywebpush cryptography
```

Gere o par de chaves VAPID uma vez (há utilitários; ou via `cryptography`) e
guarde no ambiente:

```python
# settings.py
VAPID_PUBLIC_KEY = os.environ["VAPID_PUBLIC_KEY"]
VAPID_PRIVATE_KEY = os.environ["VAPID_PRIVATE_KEY"]
VAPID_ADMIN_EMAIL = "mailto:admin@meublog.com"
```

## Possibilidades

### 1. Guardar a subscription (modelo)

```python
# apps/push/models.py
from django.conf import settings
from django.db import models


class PushSubscription(models.Model):
    """A browser's push subscription for a user."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=200)   # chave pública do cliente
    auth = models.CharField(max_length=100)      # segredo do cliente
    created_at = models.DateTimeField(auto_now_add=True)
```

### 2. No navegador: pedir permissão e assinar

```javascript
// registra o carteiro de plantão
const reg = await navigator.serviceWorker.register("/static/sw.js");

// pede permissão e assina
const sub = await reg.pushManager.subscribe({
  userVisibleOnly: true,
  applicationServerKey: VAPID_PUBLIC_KEY,   // a chave pública, vinda do Django
});

// manda a subscription para o Django guardar
await fetch("/push/subscribe/", {
  method: "POST",
  headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
  body: JSON.stringify(sub),
});
```

!!! note "`applicationServerKey` em navegadores antigos"
    Passar a chave VAPID como string base64url funciona no Chrome/Firefox atuais.
    Em engines mais antigas, `subscribe()` exige um `Uint8Array` — converta com o
    conhecido helper `urlBase64ToUint8Array(VAPID_PUBLIC_KEY)`. É a pegadinha nº 1
    de Web Push.

### 3. O service worker (`sw.js`, um estático)

```javascript
// mostra a notificação quando o push chega
self.addEventListener("push", (event) => {
  const data = event.data.json();
  event.waitUntil(
    self.registration.showNotification(data.title, { body: data.body })
  );
});
```

### 4. Enviar o push do Django

```python
# apps/push/services.py
import json
from pywebpush import webpush, WebPushException
from django.conf import settings

from apps.push.models import PushSubscription


def send_push(subscription: PushSubscription, title: str, body: str) -> bool:
    """Send one web push notification. Returns False if the sub is dead."""
    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
            },
            data=json.dumps({"title": title, "body": body}),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_ADMIN_EMAIL},
        )
        return True
    except WebPushException as exc:
        if exc.response is not None and exc.response.status_code == 410:
            subscription.delete()      # (1)!
        return False
```

1. Status **410 Gone** = a subscription morreu (usuário revogou/limpou). Apague-a
    do banco, senão você acumula lixo e tenta enviar para sempre.

!!! tip "Combine com Celery"
    Enviar push para milhares de subscriptions é lento e falha às vezes. Faça
    numa [tarefa Celery](celery.md), não no request:
    ```python
    send_push_to_all.delay(post.id)
    ```

## Gotchas

!!! danger "HTTPS é obrigatório (menos em localhost)"
    Service workers e push só funcionam sob **HTTPS**. A exceção é `localhost`
    para desenvolvimento. Em produção sem TLS, nada de push.

!!! warning "Limpe subscriptions mortas"
    Navegadores expiram/revogam subscriptions o tempo todo. Trate o **410** (como
    acima) e remova. Sem isso, sua tabela incha e cada envio desperdiça tentativas.

!!! info "iOS tem regras próprias"
    O push web no Safari/iOS exige que o site seja instalado como PWA (tela
    inicial) e tem limitações. Teste no alvo real; não assuma paridade com
    Chrome/Firefox.

## Recapitulando

- Web Push notifica **com o site fechado**, via **service worker** + push service
  do navegador + assinatura **VAPID**.
- Fluxo: navegador assina → Django guarda a **subscription** → Django envia com
  `pywebpush` (chave privada VAPID) → push service entrega → service worker mostra.
- Trate **410** apagando subscriptions mortas; envie em massa via [Celery](celery.md).
- **HTTPS** obrigatório (exceto localhost); iOS tem regras de PWA.

!!! quote "📖 Na documentação oficial"
    - [pywebpush](https://github.com/web-push-libs/pywebpush)
    - [Push API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Push_API)

Real-time e notificações cobertos. Bora filtrar listagens e APIs:
**[django-filter](django-filter.md)**.
