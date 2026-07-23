# Serviços em contêiner (Postgres, Redis, RabbitMQ, MinIO, Flower)

Um projeto Django "de gente grande" quase nunca é só o app: tem banco, cache,
fila de mensagens, armazenamento de arquivos, worker de tarefas. Em vez de
instalar tudo na sua máquina, você sobe cada um num **contêiner**. Esta página é
o cardápio pronto — copie o serviço que precisar para o seu `docker-compose.yml`.

!!! quote "Pensa como criança 🧒"
    Cada serviço é um **eletrodoméstico** da cozinha: a geladeira (banco), o
    micro-ondas rápido (cache), a esteira de pedidos (fila), o depósito (arquivos).
    O Docker Compose é a planta da cozinha: você lista os aparelhos e como eles se
    ligam na tomada (rede). Um comando e a cozinha inteira liga montada.

!!! info "Base: o deploy com Docker"
    Esta página assume que você já viu **[Deploy com Docker Compose](../referencia/deploy-docker.md)**
    (o serviço `web` do Django e o `db`). Aqui adicionamos os serviços de apoio.
    No Compose, os contêineres se acham pelo **nome do serviço** (é o "host").

## PostgreSQL — o banco

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

1. **Volume** para os dados sobreviverem a recriações do contêiner.

```python
# settings.py — Django conecta assim
DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": os.environ["DJANGO_DB_NAME"],
    "USER": os.environ["DJANGO_DB_USER"],
    "PASSWORD": os.environ["DJANGO_DB_PASSWORD"],
    "HOST": os.environ.get("DJANGO_DB_HOST", "db"),   # nome do serviço
    "PORT": "5432",
}}
```

## Redis — cache e broker

Redis é multiuso: **cache**, **broker do Celery**, **channel layer** do Channels,
**pub/sub** para SSE.

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
# settings.py — usos comuns
CACHES = {"default": {
    "BACKEND": "django.core.cache.backends.redis.RedisCache",
    "LOCATION": "redis://redis:6379/0",
}}
CELERY_BROKER_URL = "redis://redis:6379/1"
CELERY_RESULT_BACKEND = "redis://redis:6379/2"
```

!!! tip "Bancos numerados separam os usos"
    `/0`, `/1`, `/2`... são "bancos" lógicos dentro do mesmo Redis. Separe cache
    de broker de resultado para não misturar chaves.

## RabbitMQ — broker robusto (alternativa ao Redis)

Para filas maiores/críticas, o RabbitMQ é o broker clássico do Celery. Traz uma
UI de administração.

```yaml
  rabbitmq:
    image: rabbitmq:3-management         # (1)!
    environment:
      RABBITMQ_DEFAULT_USER: blog
      RABBITMQ_DEFAULT_PASS: blog
    ports:
      - "15672:15672"                    # (2)! painel web
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
```

1. A tag `-management` inclui o painel web.
2. Acesse <http://localhost:15672> (user/senha acima) para ver filas e mensagens.

```python
CELERY_BROKER_URL = "amqp://blog:blog@rabbitmq:5672//"
```

!!! info "Redis × RabbitMQ como broker"
    **Redis**: simples, você provavelmente já o tem para cache. **RabbitMQ**: mais
    recursos de roteamento e garantias, painel de administração. Para começar,
    Redis basta; migre para RabbitMQ se a fila virar peça crítica.

## MinIO — armazenamento S3 local

MinIO fala o protocolo **S3**, então você desenvolve com storage de objetos igual
à produção (AWS S3) sem pagar nuvem.

```yaml
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"      # API S3
      - "9001:9001"      # painel web
    volumes:
      - miniodata:/data
```

!!! warning "Healthcheck do MinIO tem pegadinha"
    Um `healthcheck` com `mc ready local` **não** funciona num contêiner novo: o
    alias `local` não está configurado e a imagem `minio/minio` (servidor) pode
    nem trazer o cliente `mc`. Opções que funcionam:

    - Configurar o alias antes (`mc alias set local http://localhost:9000 minioadmin
      minioadmin`) num sidecar `minio/mc`; ou
    - Fazer a checagem contra o endpoint de saúde `/minio/health/live` (a imagem
      base não tem `curl`, então use o `mc` de um sidecar ou o comando
      documentado da versão que você fixar).

    Na dúvida, omita o healthcheck do MinIO (como acima) e não use
    `condition: service_healthy` para ele.

```python
# settings.py — django-storages apontando para o MinIO
STORAGES = {"default": {"BACKEND": "storages.backends.s3.S3Storage"}}
AWS_ACCESS_KEY_ID = "minioadmin"
AWS_SECRET_ACCESS_KEY = "minioadmin"
AWS_STORAGE_BUCKET_NAME = "media"
AWS_S3_ENDPOINT_URL = "http://minio:9000"     # (1)!
```

1. O `endpoint_url` é o que faz o django-storages falar com o MinIO em vez da AWS.
    Em produção, troque pela URL real do S3. Veja [Storages](../referencia/storages.md).

## Celery worker e Flower

O **worker** reusa a **mesma imagem** do web (mesmo código), só muda o comando. O
**Flower** é o painel web que mostra tarefas, filas e workers do Celery.

```yaml
  worker:
    build: .
    command: celery -A config worker -l info
    environment:                          # (1)!
      CELERY_BROKER_URL: redis://redis:6379/1
      DJANGO_DB_HOST: db
      # ... demais envs iguais ao web ...
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

1. O worker precisa das **mesmas** variáveis do web (banco, broker) — ele roda o
    seu código e acessa o banco.
2. Painel do Flower em <http://localhost:5555>: tarefas executadas, tempo, falhas.

```bash
uv add flower      # a dependência do painel
```

!!! tip "Worker e web compartilham a imagem"
    Não faça uma imagem separada para o worker: é o mesmo projeto. `build: .` nos
    dois e mude só o `command`. Menos build, menos divergência.

## Juntando tudo

Um `docker-compose.yml` completo teria: `web` (Django/Gunicorn), `worker` +
`flower` (Celery), `db` (Postgres), `redis`, e opcionalmente `rabbitmq` e
`minio`. Cada `web`/`worker` declara `depends_on` com `condition:
service_healthy` para só subir quando as dependências estiverem prontas.

```yaml
volumes:
  pgdata:
  redisdata:
  miniodata:
```

!!! danger "Isto é base de desenvolvimento — endureça para produção"
    As senhas aqui são de exemplo. Em produção: segredos via *secrets* do
    orquestrador, TLS na frente, backups dos volumes, e limites de recurso. Veja o
    checklist em **[Deploy](../referencia/deploy.md)**.

## Recapitulando

- Cada serviço de apoio é um contêiner; no Compose eles se acham pelo **nome do
  serviço** (vira o `HOST`).
- **Postgres** (banco, com volume + healthcheck), **Redis** (cache/broker/channel
  layer — separe por banco `/0`,`/1`), **RabbitMQ** (broker robusto + painel
  15672), **MinIO** (S3 local via `AWS_S3_ENDPOINT_URL`).
- **Celery worker** reusa a imagem do web (só muda o `command`); **Flower**
  (porta 5555) monitora as tarefas.
- Use `depends_on: condition: service_healthy`; senhas de exemplo só em dev.

!!! quote "📖 Na documentação oficial"
    - [Awesome Compose (exemplos oficiais)](https://github.com/docker/awesome-compose)
    - [MinIO](https://min.io/docs/minio/container/index.html)
    - [Flower](https://flower.readthedocs.io/)

Volte ao [mapa das bibliotecas](index.md) ou ao
[deploy com Docker](../referencia/deploy-docker.md).
