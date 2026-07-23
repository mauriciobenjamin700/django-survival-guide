# Celery

Algumas tarefas são lentas: enviar e-mail, gerar um PDF, processar um vídeo,
chamar uma API externa. Fazer isso **dentro** do request deixa o usuário
esperando. O **Celery** roda essas tarefas em **segundo plano**, fora do ciclo
web.

!!! quote "Pensa como criança 🧒"
    Você pede um bolo na padaria. O atendente não fica parado assando enquanto
    você espera no balcão — ele **anota o pedido** (fila) e um padeiro nos fundos
    (worker) assa. Você recebe uma senha e segue sua vida. Celery é essa cozinha
    dos fundos: o request anota a tarefa e volta na hora; o worker executa depois.

## As peças

```mermaid
flowchart LR
    D["Django (view)"] -->|.delay(...)| B["Broker<br/>(Redis/RabbitMQ)"]
    B --> W["Worker Celery<br/>(processo separado)"]
    W -->|resultado| R["Backend de resultado<br/>(opcional)"]
```

- **Broker** — a fila de pedidos (normalmente **Redis** ou RabbitMQ).
- **Worker** — um processo separado que pega tarefas da fila e executa.
- **Backend de resultado** (opcional) — guarda o retorno da tarefa.

!!! info "Celery precisa de um broker rodando"
    Diferente de outras libs, o Celery **não** é só um `pip install`: ele exige
    um broker (um Redis, por exemplo) no ar e um **processo worker** separado do
    servidor web. É infraestrutura, não só código.

## Instalação e configuração

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

1. Lê as configs do `settings.py` que começam com `CELERY_`.
2. Procura um `tasks.py` em cada app instalado.

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

## Possibilidades

### Escrever e chamar uma tarefa

```python
# apps/blog/tasks.py
from celery import shared_task

from apps.blog.models import Post


@shared_task
def notify_subscribers(post_id: int) -> int:
    """Send a notification for a published post. Returns how many were sent."""
    post = Post.objects.get(pk=post_id)
    # ... enviar e-mails ...
    return post.title and 1 or 0
```

```python
# na view/serializer — dispara e volta na hora
from apps.blog.tasks import notify_subscribers

def publish(post):
    post.status = "published"
    post.save()
    notify_subscribers.delay(post.id)     # (1)!
```

1. **`.delay(...)`** enfileira a tarefa e retorna imediatamente — o usuário não
    espera. Passe **ids**, não objetos (veja o aviso abaixo).

!!! danger "Passe ids simples, não objetos do Django"
    Argumentos de tarefa são **serializados** (JSON por padrão) para ir na fila.
    Um objeto `Post` inteiro não serializa bem e pode chegar desatualizado ao
    worker. Passe `post.id` e recarregue com `Post.objects.get(pk=...)` dentro da
    tarefa.

### `delay` × `apply_async`

```python
notify_subscribers.delay(post.id)                       # simples
notify_subscribers.apply_async(args=[post.id], countdown=60)  # daqui a 60s
notify_subscribers.apply_async(args=[post.id], retry=True)     # reenvia ao broker se a conexão falhar
```

!!! info "Retry de conexão × retry da tarefa"
    O `retry=True` do `apply_async` reenvia a **mensagem ao broker** se a conexão
    cair — não re-executa a tarefa se ela falhar. Para repetir a **execução** ao
    dar erro, use `@shared_task(autoretry_for=(Exception,), retry_backoff=True)`
    ou `self.retry(...)` dentro da tarefa (com `bind=True`).

### Rodar o worker

```bash
celery -A config worker -l info
```

Em produção, o worker é um serviço separado (systemd, contêiner) que fica no ar
junto do web.

### Tarefas agendadas (Celery Beat)

Pensa como criança: um **despertador** que dispara tarefas em horários certos
("todo dia às 8h, mande o resumo").

```python
# settings.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "resumo-diario": {
        "task": "apps.blog.tasks.send_daily_digest",
        "schedule": crontab(hour=8, minute=0),
    },
}
```

```bash
celery -A config beat -l info      # processo do agendador
```

### Disparar só após o commit

!!! danger "Combine com transaction.on_commit"
    Se você dispara `.delay()` dentro de uma transação que depois faz rollback, o
    worker roda para um dado que não existe. Envolva:
    ```python
    from django.db import transaction
    transaction.on_commit(lambda: notify_subscribers.delay(post.id))
    ```
    Veja [transações](../referencia/transactions.md).

## Quando usar (e alternativas)

!!! tip "Use Celery quando..."
    Há tarefas lentas, agendadas ou que devem sobreviver a picos (fila). É o
    padrão da indústria em Django.

!!! warning "Talvez seja demais se..."
    Você só precisa de algo simples e esporádico. Alternativas mais leves:
    **django-q2**, **Huey**, ou até um [management command](../referencia/management-commands.md)
    disparado por cron. Celery traz broker + worker + beat — bastante
    infraestrutura.

## Recapitulando

- Celery roda tarefas **fora do request**: broker (fila) + worker (executor) +
  backend de resultado opcional.
- Precisa de infra: um Redis/RabbitMQ e um **processo worker** separado.
- Defina em `tasks.py` com `@shared_task`; dispare com `.delay(id)` (passe ids!).
- `apply_async` para agendar/retry; **Celery Beat** para tarefas periódicas.
- Combine com `transaction.on_commit` para não disparar em rollback.

!!! quote "📖 Na documentação oficial"
    - [Celery](https://docs.celeryq.dev/)
    - [First steps with Django](https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html)

Tarefas em segundo plano prontas. E comunicação em **tempo real**?
**[Django Channels](channels.md)**.
