# Referência: deploy com Docker Compose

!!! quote "Pensa como criança 🧒"
    Levar o app para produção é como mudar de casa com vários móveis: o Django, o
    banco de dados, os arquivos. O **Docker** põe cada móvel numa **caixa
    lacrada** (contêiner) que funciona igual em qualquer lugar. O **Docker
    Compose** é a lista de mudança: "quero uma caixa do app e uma caixa do banco,
    e elas conversam assim". Você dá um comando e a casa inteira sobe montada.

## Caso de uso

Você quer subir o blog em produção com **PostgreSQL**, migrações aplicadas e
estáticos servidos — tudo com um comando:

```bash
docker compose up -d --build
```

Isso sobe dois contêineres: o banco (`db`) e o app (`web`). O app espera o banco
ficar saudável, roda `migrate` e `collectstatic`, e serve com **Gunicorn**. Abra
<http://localhost:8000/>. Para dados de exemplo:

```bash
docker compose exec web python manage.py seed_blog
```

!!! check "Isto roda de verdade"
    Os arquivos [`Dockerfile`](https://github.com/mauriciobenjamin700/django-survival-guide/blob/main/Dockerfile),
    [`docker-compose.yml`](https://github.com/mauriciobenjamin700/django-survival-guide/blob/main/docker-compose.yml)
    e [`docker/entrypoint.sh`](https://github.com/mauriciobenjamin700/django-survival-guide/blob/main/docker/entrypoint.sh)
    estão no repositório e foram testados subindo o stack completo.

## Possibilidades

### O `Dockerfile`: a receita da caixa do app

```dockerfile
# syntax=docker/dockerfile:1

FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv   # (1)!

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --group prod --no-install-project   # (2)!

COPY example/ ./example/
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /app/example

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
```

1. Copia o binário do `uv` de uma imagem oficial — instala dependências rápido.
2. Instala **só** o necessário para produção: `--no-dev` (sem pytest/mkdocs) e
    `--group prod` (gunicorn, whitenoise, psycopg). `--frozen` respeita o
    `uv.lock`.

!!! tip "Camadas: copie o lock ANTES do código"
    Copiar `pyproject.toml`/`uv.lock` e instalar **antes** de copiar `example/`
    faz o Docker cachear a camada de dependências. Mudou só o código? O rebuild
    não reinstala tudo. Pensa como criança: guarde os brinquedos pesados no fundo
    da mochila; você não os tira toda vez.

### O `entrypoint.sh`: o que roda quando a caixa abre

```sh
#!/bin/sh
set -e

python manage.py migrate --no-input
python manage.py collectstatic --no-input

exec "$@"
```

- Aplica migrações e coleta estáticos **toda vez** que o contêiner sobe.
- `exec "$@"` entrega o controle ao `CMD` (o Gunicorn) — sem deixar um processo
  extra pendurado.

!!! warning "Migração automática no start: bom para começar, cuidado ao escalar"
    Rodar `migrate` no entrypoint é ótimo para 1 instância. Com **várias**
    réplicas subindo juntas, todas tentariam migrar ao mesmo tempo. Aí mova o
    `migrate` para um passo separado do deploy (um job/`docker compose run web
    python manage.py migrate`) antes de subir as réplicas.

### O `docker-compose.yml`: a lista de mudança

```yaml
services:
  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: blog
      POSTGRES_USER: blog
      POSTGRES_PASSWORD: blog
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U blog"]
      interval: 5s
      timeout: 3s
      retries: 5

  web:
    build: .
    environment:
      DJANGO_DEBUG: "false"
      DJANGO_SECRET_KEY: "change-me-in-production"
      DJANGO_ALLOWED_HOSTS: "localhost,127.0.0.1"
      DJANGO_DB_NAME: blog
      DJANGO_DB_USER: blog
      DJANGO_DB_PASSWORD: blog
      DJANGO_DB_HOST: db          # (1)!
      DJANGO_DB_PORT: "5432"
    volumes:
      - media:/app/example/media   # (2)!
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy  # (3)!

volumes:
  pgdata:
  media:
```

1. O host do banco é **`db`** — o nome do serviço. No Compose, os contêineres se
    acham pelo nome do serviço, como se fosse um DNS interno.
2. Um **volume** para os uploads sobreviverem a rebuilds do contêiner.
3. O `web` só sobe **depois** que o `db` passa no `healthcheck` — sem isso, o app
    tentaria conectar antes do banco estar pronto.

### Como o `settings.py` reage ao ambiente

O mesmo código roda em SQLite (dev) ou Postgres (Docker) porque o `settings`
**lê o ambiente**:

```python
if os.environ.get("DJANGO_DB_NAME"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["DJANGO_DB_NAME"],
            "USER": os.environ.get("DJANGO_DB_USER", "postgres"),
            "PASSWORD": os.environ.get("DJANGO_DB_PASSWORD", ""),
            "HOST": os.environ.get("DJANGO_DB_HOST", "localhost"),
            "PORT": os.environ.get("DJANGO_DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
```

E os estáticos são servidos pelo **WhiteNoise** (sem precisar de Nginx para o
básico):

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",   # logo após o security
    # ...
]
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
```

### Comandos do dia a dia

| Comando | Faz |
| --- | --- |
| `docker compose up -d --build` | Sobe tudo (rebuild da imagem) |
| `docker compose logs -f web` | Acompanha os logs do app |
| `docker compose exec web python manage.py seed_blog` | Roda um comando dentro do app |
| `docker compose exec web python manage.py createsuperuser` | Cria admin |
| `docker compose ps` | Mostra o estado dos serviços |
| `docker compose down` | Derruba (mantém os volumes) |
| `docker compose down -v` | Derruba **e apaga** os volumes (dados!) |

### `.dockerignore`: não empacote lixo

```text
.git
.venv
*.sqlite3
site/
docs/
example/staticfiles/
example/media/
```

!!! tip "Contexto enxuto = build rápido"
    O `.dockerignore` impede que `.venv`, o banco SQLite de dev, o site gerado e a
    pasta `docs/` entrem na imagem. Menos coisa para copiar, build mais rápido e
    imagem menor.

### O que falta para produção "de verdade"

!!! danger "Este stack é uma base sólida — endureça antes de expor"
    - **`SECRET_KEY` e senhas** via *secrets* do orquestrador, nunca fixas no
      `compose` como aqui (é só demonstração).
    - **HTTPS**: ponha um Nginx/Traefik ou um load balancer na frente,
      terminando TLS. Ligue `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`,
      `CSRF_COOKIE_SECURE`, HSTS (ver [deploy](deploy.md)).
    - **Backups** do volume do Postgres.
    - **`migrate` como passo separado** ao escalar réplicas.
    - Rode `python manage.py check --deploy` e resolva os avisos.

## Recap

- Docker empacota o app numa caixa; Compose orquestra app + banco com um comando.
- `Dockerfile`: `uv sync --no-dev --group prod`, copie o lock antes do código
  (cache de camadas).
- `entrypoint.sh` roda `migrate` + `collectstatic` e entrega ao Gunicorn.
- `docker-compose.yml`: serviço `db` (Postgres com healthcheck) + `web`
  (`depends_on: healthy`), acham-se pelo **nome do serviço**; volumes para dados.
- O `settings` lê o banco do **ambiente**; WhiteNoise serve os estáticos.
- Antes de expor: secrets, HTTPS, backups, `migrate` separado, `check --deploy`.

Para o checklist geral de produção (sem Docker), veja **[deploy](deploy.md)**.
