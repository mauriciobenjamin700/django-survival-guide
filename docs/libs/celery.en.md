# Celery

Some tasks are slow: sending an email, generating a PDF, processing a video,
calling an external API. Doing that **inside** the request keeps the user
waiting. **Celery** runs those tasks in the **background**, outside the web
cycle.

!!! quote "Think like a child 🧒"
    You order a cake at the bakery. The clerk doesn't stand there baking while
    you wait at the counter — they **write down the order** (queue) and a baker in the back
    (worker) bakes it. You get a ticket and get on with your life. Celery is that back
    kitchen: the request writes down the task and returns immediately; the worker runs it later.

## The pieces

```mermaid
flowchart LR
    D["Django (view)"] -->|.delay(...)| B["Broker<br/>(Redis/RabbitMQ)"]
    B --> W["Celery worker<br/>(separate process)"]
    W -->|result| R["Result backend<br/>(optional)"]
```

- **Broker** — the order queue (usually **Redis** or RabbitMQ).
- **Worker** — a separate process that picks tasks off the queue and runs them.
- **Result backend** (optional) — stores the task's return value.

!!! info "Celery needs a running broker"
    Unlike other libs, Celery is **not** just a `pip install`: it requires
    a broker (a Redis, for example) up and running and a **worker process** separate from the
    web server. It's infrastructure, not just code.

## Installation and configuration

```bash
uv add celery redis
```

```python
# config/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")  # (1)!
app.autodiscover_tasks()                                            # (2)!
```

1. Reads the `settings.py` configs that start with `CELERY_`.
2. Looks for a `tasks.py` in each installed app.

```python
# config/__init__.py
from config.celery import app as celery_app

__all__ = ("celery_app",)
```

```python
# settings.py
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
CELERY_TASK_TIME_LIMIT = 300
```

## What you can do

### Write and call a task

```python
# apps/blog/tasks.py
from celery import shared_task

from apps.blog.models import Post


@shared_task
def notify_subscribers(post_id: int) -> int:
    """Send a notification for a published post. Returns how many were sent."""
    post = Post.objects.get(pk=post_id)
    # ... send emails ...
    return post.title and 1 or 0
```

```python
# in the view/serializer — fires and returns immediately
from apps.blog.tasks import notify_subscribers

def publish(post):
    post.status = "published"
    post.save()
    notify_subscribers.delay(post.id)     # (1)!
```

1. **`.delay(...)`** enqueues the task and returns immediately — the user doesn't
    wait. Pass **ids**, not objects (see the warning below).

!!! danger "Pass plain ids, not Django objects"
    Task arguments are **serialized** (JSON by default) to go on the queue.
    A whole `Post` object doesn't serialize well and may arrive stale at the
    worker. Pass `post.id` and reload with `Post.objects.get(pk=...)` inside the
    task.

### `delay` vs `apply_async`

```python
notify_subscribers.delay(post.id)                       # simple
notify_subscribers.apply_async(args=[post.id], countdown=60)  # 60s from now
notify_subscribers.apply_async(args=[post.id], retry=True)     # resend to broker if the connection fails
```

!!! info "Connection retry × task retry"
    `apply_async`'s `retry=True` re-sends the **message to the broker** if the
    connection drops — it does not re-run the task if it fails. To retry the
    **execution** on error, use `@shared_task(autoretry_for=(Exception,),
    retry_backoff=True)` or `self.retry(...)` inside the task (with `bind=True`).

### Run the worker

```bash
celery -A config worker -l info
```

In production, the worker is a separate service (systemd, container) that stays running
alongside the web.

### Scheduled tasks (Celery Beat)

Think like a child: an **alarm clock** that fires tasks at set times
("every day at 8am, send the digest").

```python
# settings.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "daily-digest": {
        "task": "apps.blog.tasks.send_daily_digest",
        "schedule": crontab(hour=8, minute=0),
    },
}
```

```bash
celery -A config beat -l info      # the scheduler process
```

### Fire only after commit

!!! danger "Combine with transaction.on_commit"
    If you fire `.delay()` inside a transaction that later rolls back, the
    worker runs against data that doesn't exist. Wrap it:
    ```python
    from django.db import transaction
    transaction.on_commit(lambda: notify_subscribers.delay(post.id))
    ```
    See [transactions](../referencia/transactions.md).

## When to use it (and alternatives)

!!! tip "Use Celery when..."
    There are slow, scheduled, or peak-surviving (queued) tasks. It's the
    industry standard in Django.

!!! warning "It may be overkill if..."
    You just need something simple and occasional. Lighter alternatives:
    **django-q2**, **Huey**, or even a [management command](../referencia/management-commands.md)
    fired by cron. Celery brings broker + worker + beat — quite a lot of
    infrastructure.

## Recap

- Celery runs tasks **outside the request**: broker (queue) + worker (executor) +
  optional result backend.
- Needs infra: a Redis/RabbitMQ and a separate **worker process**.
- Define them in `tasks.py` with `@shared_task`; fire them with `.delay(id)` (pass ids!).
- `apply_async` to schedule/retry; **Celery Beat** for periodic tasks.
- Combine with `transaction.on_commit` so you don't fire on rollback.

!!! quote "📖 In the official docs"
    - [Celery](https://docs.celeryq.dev/)
    - [First steps with Django](https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html)

Background tasks ready. And real-time communication?
**[Django Channels](channels.md)**.
