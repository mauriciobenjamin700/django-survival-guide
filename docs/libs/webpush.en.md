# Web Push (notifications)

SSE and WebSocket only deliver while the tab is **open**. **Web Push** goes further:
it notifies the user even with the site **closed** — like a phone app. It's what
Django needs to feel as "modern" as a React/mobile app.

!!! quote "Think like a child 🧒"
    SSE/WebSocket is talking to someone who's in the room. Web Push is sending a
    **letter that shows up at the door** even when the house is empty — the mail carrier
    (the browser's push service) delivers it, and they see it when it arrives. It works
    because the browser left a **mail carrier on duty** (the service worker).

## The pieces (and why there are so many)

```mermaid
flowchart LR
    U["Browser<br/>(service worker)"] -->|1. subscribes, gives the subscription| D["Django"]
    D -->|2. stores the subscription| DB["Database"]
    D -->|3. sends signed push (VAPID)| P["Push service<br/>(Google/Mozilla)"]
    P -->|4. delivers the notification| U
```

- **Service worker** — a script the browser keeps running in the background,
  even with the tab closed. It's the one that receives and shows the notification.
- **Subscription** — the "mailbox" of that browser (a URL + keys),
  generated when the user **allows** notifications. You store it in the database.
- **VAPID** — a key pair (public/private) that **signs** the sends, proving
  it's you. The push service requires it.
- **Push service** — the browser's own infrastructure (Google/Mozilla), not yours.

## Installation and keys

```bash
uv add pywebpush cryptography
```

Generate the VAPID key pair once (there are utilities; or via `cryptography`) and
store it in the environment:

```python
# settings.py
VAPID_PUBLIC_KEY = os.environ["VAPID_PUBLIC_KEY"]
VAPID_PRIVATE_KEY = os.environ["VAPID_PRIVATE_KEY"]
VAPID_ADMIN_EMAIL = "mailto:admin@myblog.com"
```

## What you can do

### 1. Store the subscription (model)

```python
# apps/push/models.py
from django.conf import settings
from django.db import models


class PushSubscription(models.Model):
    """A browser's push subscription for a user."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=200)   # client's public key
    auth = models.CharField(max_length=100)      # client's secret
    created_at = models.DateTimeField(auto_now_add=True)
```

### 2. In the browser: ask for permission and subscribe

```javascript
// register the mail carrier on duty
const reg = await navigator.serviceWorker.register("/static/sw.js");

// ask for permission and subscribe
const sub = await reg.pushManager.subscribe({
  userVisibleOnly: true,
  applicationServerKey: VAPID_PUBLIC_KEY,   // the public key, coming from Django
});

// send the subscription to Django to store
await fetch("/push/subscribe/", {
  method: "POST",
  headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
  body: JSON.stringify(sub),
});
```

!!! note "`applicationServerKey` on older browsers"
    Passing the VAPID key as a base64url string works in current Chrome/Firefox.
    On older engines, `subscribe()` requires a `Uint8Array` — convert it with the
    well-known `urlBase64ToUint8Array(VAPID_PUBLIC_KEY)` helper. It's the #1 Web
    Push gotcha.

### 3. The service worker (`sw.js`, a static file)

```javascript
// show the notification when the push arrives
self.addEventListener("push", (event) => {
  const data = event.data.json();
  event.waitUntil(
    self.registration.showNotification(data.title, { body: data.body })
  );
});
```

### 4. Send the push from Django

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

1. Status **410 Gone** = the subscription died (the user revoked/cleared it). Delete it
    from the database, otherwise you pile up garbage and try to send forever.

!!! tip "Combine with Celery"
    Sending push to thousands of subscriptions is slow and sometimes fails. Do it
    in a [Celery task](celery.md), not in the request:
    ```python
    send_push_to_all.delay(post.id)
    ```

## Gotchas

!!! danger "HTTPS is mandatory (except on localhost)"
    Service workers and push only work under **HTTPS**. The exception is `localhost`
    for development. In production without TLS, no push.

!!! warning "Clean up dead subscriptions"
    Browsers expire/revoke subscriptions all the time. Handle the **410** (as
    above) and remove them. Without that, your table bloats and every send wastes attempts.

!!! info "iOS has its own rules"
    Web push on Safari/iOS requires the site to be installed as a PWA (home
    screen) and has limitations. Test on the real target; don't assume parity with
    Chrome/Firefox.

## Recap

- Web Push notifies **with the site closed**, via a **service worker** + the browser's push service
  + a **VAPID** signature.
- Flow: browser subscribes → Django stores the **subscription** → Django sends with
  `pywebpush` (VAPID private key) → push service delivers → service worker shows it.
- Handle **410** by deleting dead subscriptions; send in bulk via [Celery](celery.md).
- **HTTPS** mandatory (except localhost); iOS has PWA rules.

!!! quote "📖 In the official docs"
    - [pywebpush](https://github.com/web-push-libs/pywebpush)
    - [Push API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Push_API)

Real-time and notifications covered. Let's filter listings and APIs:
**[django-filter](django-filter.md)**.
