# Afins: o catálogo essencial

Além das grandes (allauth, Celery, Channels), há um punhado de bibliotecas que
aparecem em quase todo projeto Django sério. Aqui vai o catálogo com o **para quê**
e o mínimo para começar.

!!! quote "Pensa como criança 🧒"
    São as **ferramentas da caixa**: a lanterna que mostra o que está travando
    (debug), a chave que organiza segredos (environ), o megafone que documenta a
    API. Você não usa todas sempre, mas é bom saber que existem quando precisar.

## Desenvolvimento

### django-debug-toolbar — a lanterna

Mostra, em cada página, as **queries SQL**, o tempo, os templates, o cache. É a
forma nº 1 de caçar o [N+1](../referencia/querysets-api.md).

```bash
uv add django-debug-toolbar
```
```python
INSTALLED_APPS = ["debug_toolbar", ...]
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware", ...]
INTERNAL_IPS = ["127.0.0.1"]
# urls.py: path("__debug__/", include("debug_toolbar.urls"))
```

!!! danger "Só em desenvolvimento"
    A toolbar expõe dados internos. Ative **apenas** com `DEBUG=True`; nunca a
    deixe num ambiente público.

### django-extensions — o canivete

`shell_plus` (shell com todos os models já importados), `runserver_plus`,
`graph_models` (diagrama do ORM), `show_urls`.

```bash
uv add django-extensions
# INSTALLED_APPS += ["django_extensions"]
python manage.py shell_plus
```

## Configuração

### django-environ — a chave dos segredos

Lê `.env` e converte tipos, deixando o [settings](../referencia/settings.md) limpo.

```bash
uv add django-environ
```
```python
import environ
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DEBUG")
DATABASES = {"default": env.db("DATABASE_URL")}   # parseia postgres://... sozinho
```

## API (DRF)

### djangorestframework-simplejwt — login por token

Para APIs consumidas por app mobile/SPA, o fluxo é **JWT**, não sessão/cookie.

```bash
uv add djangorestframework-simplejwt
```
```python
# urls.py
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
path("api/token/", TokenObtainPairView.as_view()),
path("api/token/refresh/", TokenRefreshView.as_view()),
```
O cliente manda `Authorization: Bearer <token>` nas requisições.

### drf-spectacular — documentação OpenAPI

Gera um schema **OpenAPI 3** e uma UI (Swagger/Redoc) navegável da sua API,
lendo os serializers/viewsets.

```bash
uv add drf-spectacular
```
```python
REST_FRAMEWORK = {"DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema"}
# urls.py: SpectacularAPIView (schema) + SpectacularSwaggerView (UI)
```

### django-cors-headers — liberar o front separado

Se o front (React/Vite) roda em **outra origem** (`localhost:5173`) e chama sua
API, o navegador bloqueia por CORS. Esta lib libera as origens certas.

```bash
uv add django-cors-headers
```
```python
INSTALLED_APPS = ["corsheaders", ...]
MIDDLEWARE = ["corsheaders.middleware.CorsMiddleware", ...]  # bem no topo
CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]
```

!!! warning "CORS não é segurança — é permissão de navegador"
    Nunca use `CORS_ALLOW_ALL_ORIGINS = True` em produção. Liste as origens
    exatas. E lembre: CORS controla o **navegador**, não substitui autenticação.

## Arquivos e imagens

### Pillow — imagens

Necessário para o `ImageField` e para redimensionar/validar imagens.

```bash
uv add pillow
```

### django-storages + WhiteNoise

Armazenamento em nuvem (S3) e estáticos em produção — cobertos em
**[Storages](../referencia/storages.md)** e **[static-media](../referencia/static-media.md)**.

## Tabela-resumo

| Biblioteca | Categoria | Para quê |
| --- | --- | --- |
| django-debug-toolbar | Dev | Ver SQL/tempo/queries (caçar N+1) |
| django-extensions | Dev | `shell_plus`, diagramas, utilidades |
| django-environ | Config | Ler `.env` tipado |
| djangorestframework-simplejwt | API | Autenticação por JWT |
| drf-spectacular | API | Documentação OpenAPI/Swagger |
| django-cors-headers | API | Liberar front de outra origem |
| Pillow | Arquivos | Imagens (`ImageField`) |
| django-storages | Arquivos | Uploads em nuvem (S3/GCS/Azure) |

!!! tip "Não instale tudo de uma vez"
    Adicione uma lib quando o problema aparecer, não "por precaução". Cada
    dependência é manutenção. As de **dev** (toolbar, extensions) só no grupo de
    desenvolvimento (`uv add --group dev ...`).

## Recapitulando

- **Dev**: debug-toolbar (SQL/queries, só em `DEBUG`), extensions (`shell_plus`).
- **Config**: django-environ (`.env` tipado).
- **API**: simplejwt (JWT), drf-spectacular (OpenAPI), cors-headers (front
  separado — CORS não é segurança).
- **Arquivos**: Pillow (imagens), django-storages (nuvem).
- Instale sob demanda; libs de dev no grupo `dev`.

Voltando à infraestrutura: como subir tudo isso em contêineres —
**[serviços em contêiner](containers.md)**.
