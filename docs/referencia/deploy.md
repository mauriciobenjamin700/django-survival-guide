# Referência: deploy

!!! quote "Pensa como criança 🧒"
    Até agora você brincou dentro de casa (o `runserver`, só para você). **Deploy**
    é levar o brinquedo para a pracinha, onde qualquer um pode usar. Lá fora tem
    regras diferentes: a porta tem que estar trancada (`DEBUG=False`), um adulto
    de verdade cuida do portão (Gunicorn, não o `runserver`), e os brinquedos
    fixos (CSS, imagens) ficam numa caixa organizada (arquivos estáticos).

## Caso de uso

Você quer pôr o blog no ar com segurança. O caminho: ajustar settings via
ambiente, coletar os estáticos, e servir com um servidor de produção:

```bash
# 1. Conferir se está pronto para produção
DJANGO_DEBUG=false python manage.py check --deploy

# 2. Juntar os arquivos estáticos num lugar só
python manage.py collectstatic --no-input

# 3. Aplicar migrações
python manage.py migrate

# 4. Servir com Gunicorn (não com runserver!)
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

## Possibilidades

### O `runserver` é só para desenvolvimento

!!! danger "Nunca use `runserver` em produção"
    Ele é single-thread, sem otimização, e o próprio Django avisa que não é para
    isso. Em produção, um **servidor WSGI/ASGI** cuida das requisições:
    Gunicorn ou Uvicorn.

| Tipo | Servidor | Aponta para |
| --- | --- | --- |
| WSGI (síncrono) | Gunicorn | `config.wsgi:application` |
| ASGI (assíncrono) | Uvicorn / Gunicorn+workers Uvicorn | `config.asgi:application` |

```bash
# WSGI
gunicorn config.wsgi:application --workers 3 --bind 0.0.0.0:8000

# ASGI
uvicorn config.asgi:application --host 0.0.0.0 --port 8000
```

### O checklist de segurança dos settings

Rode `python manage.py check --deploy` e resolva os avisos. Os principais:

```python
DEBUG = False                                   # nunca True em produção
ALLOWED_HOSTS = ["meublog.com", "www.meublog.com"]
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]    # do ambiente, nunca no Git

SECURE_SSL_REDIRECT = True                       # força HTTPS
SESSION_COOKIE_SECURE = True                     # cookie só via HTTPS
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000                   # HSTS (1 ano)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

!!! danger "O tripé mortal: `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`"
    - `DEBUG=True` em produção **vaza** stack traces com dados sensíveis.
    - `SECRET_KEY` no Git = qualquer um forja sessões e tokens.
    - `ALLOWED_HOSTS` vazio/`*` abre para ataques de Host header.

    Pensa como criança: são as três trancas da porta. Sair sem elas é deixar a
    casa aberta.

### Arquivos estáticos

Pensa como criança: os estáticos (CSS, JS, imagens do tema) são os brinquedos
que **não mudam**. Em produção você os junta todos numa caixa (`STATIC_ROOT`) e
alguém eficiente os entrega.

```python
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"     # onde o collectstatic junta tudo

# MEDIA = arquivos ENVIADOS por usuários (uploads) — separados dos estáticos
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
```

```bash
python manage.py collectstatic --no-input
```

!!! info "Estático × media"
    - **Estático**: vem com o projeto (CSS, JS). Você controla. `collectstatic`.
    - **Media**: enviado por usuários (avatares, anexos). Muda em runtime.

    Nunca misture os dois diretórios.

#### WhiteNoise: servir estáticos sem Nginx

Para deploys simples (Heroku, contêiner único), o **WhiteNoise** faz o próprio
Django servir os estáticos de forma eficiente:

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",   # logo após o Security
    # ...
]
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
```

### Variáveis de ambiente

Tudo que muda entre ambientes vem do ambiente, não do código:

| Variável | Exemplo |
| --- | --- |
| `DJANGO_SECRET_KEY` | (uma chave longa e aleatória) |
| `DJANGO_DEBUG` | `false` |
| `DJANGO_ALLOWED_HOSTS` | `meublog.com,www.meublog.com` |
| `DATABASE_URL` | `postgres://user:pass@host:5432/db` |

### Um `Dockerfile` mínimo

```dockerfile
FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --no-dev --frozen

COPY . .
RUN uv run python manage.py collectstatic --no-input

CMD ["uv", "run", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### A ordem certa no deploy

```mermaid
flowchart LR
    A[Novo código] --> B[migrate]
    B --> C[collectstatic]
    C --> D[Reiniciar Gunicorn]
    D --> E[Health check]
```

!!! tip "Migre antes de trocar o código que já usa o novo schema"
    Rode `migrate` **antes** de subir o processo que espera as tabelas novas. Se
    o app novo subir antes da migração, ele quebra ao acessar colunas que ainda
    não existem.

## Recap

- `runserver` **jamais** em produção — use Gunicorn (WSGI) ou Uvicorn (ASGI).
- Trave a segurança: `DEBUG=False`, `SECRET_KEY` do ambiente, `ALLOWED_HOSTS`
  restrito, cookies `Secure`, HSTS. Valide com `check --deploy`.
- Estáticos: `collectstatic` junta em `STATIC_ROOT`; **WhiteNoise** os serve em
  deploys simples. Media (uploads) fica separado.
- Configuração sensível vem de **variáveis de ambiente**.
- Ordem: `migrate` → `collectstatic` → reiniciar servidor → health check.

Você tem agora a referência do Django do modelo ao deploy. Volte ao
[Tutorial](../tutorial/project-setup.md) sempre que quiser ver tudo junto. 🎉
