# Containerized services (Postgres, Redis, RabbitMQ, MinIO, Flower)

A "grown-up" Django project is almost never just the app: it has a database, cache,
message queue, file storage, a task worker. Instead of
installing everything on your machine, you bring each one up in a **container**. This page is
the ready-made menu — copy the service you need into your `docker-compose.yml`.

!!! quote "Think like a child 🧒"
    Each service is a kitchen **appliance**: the fridge (database), the fast
    microwave (cache), the order conveyor belt (queue), the pantry (files).
    Docker Compose is the kitchen blueprint: you list the appliances and how they
    plug into the socket (network). One command and the whole kitchen powers up assembled.

!!! info "Base: the Docker deploy"
    This page assumes you've already seen **[Deploy with Docker Compose](../referencia/deploy-docker.md)**
    (Django's `web` service and the `db`). Here we add the support services.
    In Compose, containers find each other by the **service name** (that's the "host").

## PostgreSQL — the database

```yaml
  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: blog
      POSTGRES_USER: blog
      POSTGRES_PASSWORD: blog
    volumes:
      - pgdata:/var/lib/postgresql/data      # (1)!
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U blog"]
      interval: 5s
      timeout: 3s
      retries: 5
```

1. A **volume** so the data survives container recreations.

```python
# settings.py — Django connects like this
DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": os.environ["DJANGO_DB_NAME"],
    "USER": os.environ["DJANGO_DB_USER"],
    "PASSWORD": os.environ["DJANGO_DB_PASSWORD"],
    "HOST": os.environ.get("DJANGO_DB_HOST", "db"),   # service name
    "PORT": "5432",
}}
```

## Redis — cache and broker

Redis is multipurpose: **cache**, **Celery broker**, Channels **channel layer**,
**pub/sub** for SSE.

```yaml
  redis:
    image: redis:7-alpine
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
```

```python
# settings.py — common uses
CACHES = {"default": {
    "BACKEND": "django.core.cache.backends.redis.RedisCache",
    "LOCATION": "redis://redis:6379/0",
}}
CELERY_BROKER_URL = "redis://redis:6379/1"
CELERY_RESULT_BACKEND = "redis://redis:6379/2"
```

!!! tip "Numbered databases separate the uses"
    `/0`, `/1`, `/2`... are logical "databases" inside the same Redis. Separate cache
    from broker from result so you don't mix keys.

## RabbitMQ — a robust broker (alternative to Redis)

For larger/critical queues, RabbitMQ is Celery's classic broker. It comes with an
admin UI.

```yaml
  rabbitmq:
    image: rabbitmq:3-management         # (1)!
    environment:
      RABBITMQ_DEFAULT_USER: blog
      RABBITMQ_DEFAULT_PASS: blog
    ports:
      - "15672:15672"                    # (2)! web panel
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
```

1. The `-management` tag includes the web panel.
2. Access <http://localhost:15672> (user/password above) to see queues and messages.

```python
CELERY_BROKER_URL = "amqp://blog:blog@rabbitmq:5672//"
```

!!! info "Redis vs RabbitMQ as a broker"
    **Redis**: simple, you probably already have it for cache. **RabbitMQ**: more
    routing features and guarantees, an admin panel. To get started,
    Redis is enough; migrate to RabbitMQ if the queue becomes a critical piece.

## MinIO — local S3 storage

MinIO speaks the **S3** protocol, so you develop with object storage just like
production (AWS S3) without paying for the cloud.

```yaml
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"      # S3 API
      - "9001:9001"      # web panel
    volumes:
      - miniodata:/data
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 10s
      timeout: 5s
      retries: 5
```

```python
# settings.py — django-storages pointing at MinIO
STORAGES = {"default": {"BACKEND": "storages.backends.s3.S3Storage"}}
AWS_ACCESS_KEY_ID = "minioadmin"
AWS_SECRET_ACCESS_KEY = "minioadmin"
AWS_STORAGE_BUCKET_NAME = "media"
AWS_S3_ENDPOINT_URL = "http://minio:9000"     # (1)!
```

1. The `endpoint_url` is what makes django-storages talk to MinIO instead of AWS.
    In production, swap it for the real S3 URL. See [Storages](../referencia/storages.md).

## Celery worker and Flower

The **worker** reuses the **same image** as the web (same code), only the command changes. **Flower** is the web panel that shows Celery's tasks, queues and workers.

```yaml
  worker:
    build: .
    command: celery -A config worker -l info
    environment:                          # (1)!
      CELERY_BROKER_URL: redis://redis:6379/1
      DJANGO_DB_HOST: db
      # ... other envs same as the web ...
    depends_on:
      redis:
        condition: service_healthy
      db:
        condition: service_healthy

  flower:
    build: .
    command: celery -A config flower --port=5555
    ports:
      - "5555:5555"                        # (2)!
    environment:
      CELERY_BROKER_URL: redis://redis:6379/1
    depends_on:
      - redis
```

1. The worker needs the **same** variables as the web (database, broker) — it runs
    your code and accesses the database.
2. Flower's panel at <http://localhost:5555>: executed tasks, timing, failures.

```bash
uv add flower      # the panel's dependency
```

!!! tip "Worker and web share the image"
    Don't make a separate image for the worker: it's the same project. `build: .` on
    both and change only the `command`. Less building, less divergence.

## Putting it all together

A complete `docker-compose.yml` would have: `web` (Django/Gunicorn), `worker` +
`flower` (Celery), `db` (Postgres), `redis`, and optionally `rabbitmq` and
`minio`. Each `web`/`worker` declares `depends_on` with `condition:
service_healthy` so it only comes up when the dependencies are ready.

```yaml
volumes:
  pgdata:
  redisdata:
  miniodata:
```

!!! danger "This is a development base — harden it for production"
    The passwords here are examples. In production: secrets via the orchestrator's
    *secrets*, TLS in front, backups of the volumes, and resource limits. See the
    checklist in **[Deploy](../referencia/deploy.md)**.

## Recap

- Each support service is a container; in Compose they find each other by the **service
  name** (which becomes the `HOST`).
- **Postgres** (database, with volume + healthcheck), **Redis** (cache/broker/channel
  layer — separate by database `/0`,`/1`), **RabbitMQ** (robust broker + panel
  15672), **MinIO** (local S3 via `AWS_S3_ENDPOINT_URL`).
- **Celery worker** reuses the web image (only the `command` changes); **Flower**
  (port 5555) monitors the tasks.
- Use `depends_on: condition: service_healthy`; example passwords in dev only.

!!! quote "📖 In the official docs"
    - [Awesome Compose (official examples)](https://github.com/docker/awesome-compose)
    - [MinIO](https://min.io/docs/minio/container/index.html)
    - [Flower](https://flower.readthedocs.io/)

Go back to the [library map](index.md) or to the
[Docker deploy](../referencia/deploy-docker.md).
