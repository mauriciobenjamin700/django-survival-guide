# Configurando o projeto

Antes de escrever qualquer funcionalidade, precisamos entender **como um projeto
Django é organizado**. Django separa dois conceitos:

- **Projeto** — a configuração geral (settings, URLs raiz, WSGI/ASGI).
- **App** — um módulo com uma responsabilidade (aqui, o `blog`).

Um projeto contém vários apps. Cada app deve fazer *uma* coisa bem feita.

## A estrutura que usamos

```text
example/
├── manage.py                 # ponto de entrada dos comandos
├── config/                   # o "projeto": configuração geral
│   ├── settings.py           # todas as configurações
│   ├── urls.py               # roteamento raiz
│   ├── wsgi.py / asgi.py     # servidores de produção
└── apps/
    └── blog/                 # o "app": nossa funcionalidade
        ├── apps.py           # configuração do app
        ├── models.py         # tabelas do banco
        ├── views.py          # lógica de requisição/resposta
        ├── urls.py           # rotas do app
        ├── forms.py          # formulários
        ├── admin.py          # configuração do admin
        └── templates/        # HTML
```

!!! info "Por que uma pasta `apps/`?"
    O `startproject` gera os apps na raiz por padrão. Colocá-los sob `apps/`
    mantém a raiz limpa e deixa claro o que é *seu código* versus configuração.
    É uma convenção comum em projetos maiores.

## Como criamos

```bash
uv run django-admin startproject config .
mkdir -p apps/blog
touch apps/__init__.py          # torna 'apps' um pacote importável
uv run python manage.py startapp blog apps/blog
```

## O `settings.py` — sem mágica

O `settings.py` é só um **módulo Python com variáveis de nível de módulo** que o
Django lê ao iniciar. Nada de formato especial. Veja como tornamos os valores
sensíveis a ambiente, com padrões amigáveis para desenvolvimento:

```python
import os
from pathlib import Path

BASE_DIR: Path = Path(__file__).resolve().parent.parent

SECRET_KEY: str = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-only-change-me-in-production",
)

DEBUG: bool = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"

ALLOWED_HOSTS: list[str] = os.environ.get(
    "DJANGO_ALLOWED_HOSTS",
    "localhost,127.0.0.1",
).split(",")
```

!!! tip "Tipagem em settings"
    Anotar `BASE_DIR: Path`, `DEBUG: bool` etc. não muda o comportamento, mas
    documenta o tipo esperado e ajuda o editor. É o nosso princípio de *tipagem
    clara* aplicado até na configuração.

!!! warning "`SECRET_KEY` e `DEBUG` em produção"
    Nunca use a `SECRET_KEY` padrão em produção, e sempre rode com `DEBUG=false`.
    Por isso lemos ambos de variáveis de ambiente: em produção você define
    `DJANGO_SECRET_KEY` e `DJANGO_DEBUG=false` sem tocar no código.

### Registrando o app

Para o Django "enxergar" o blog, ele entra em `INSTALLED_APPS`:

```python
INSTALLED_APPS: list[str] = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.blog",  # (1)!
]
```

1. Note o caminho `apps.blog`: é o caminho de importação Python real, porque o
   app vive em `apps/blog/`.

Como o app está em `apps/blog/`, o `apps.py` declara o caminho e um `label`
curto para as tabelas não ficarem com nome gigante:

```python
from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field: str = "django.db.models.BigAutoField"
    name: str = "apps.blog"   # caminho de importação
    label: str = "blog"       # tabelas viram blog_post, blog_tag...
```

!!! note "`name` vs `label`"
    - `name` é o **caminho de importação** (`apps.blog`) — precisa bater com a
      pasta real.
    - `label` é o **apelido interno** usado em nomes de tabela e migrações. Sem
      ele, as tabelas seriam `apps_blog_post` em vez de `blog_post`.

## O `manage.py`

É o canivete suíço do projeto. Todo comando administrativo passa por ele:

```bash
uv run python manage.py <comando>
```

Alguns que já vamos usar: `migrate`, `makemigrations`, `runserver`,
`createsuperuser`, `shell`, `test`.

!!! quote "📖 Na documentação oficial"
    - [Applications](https://docs.djangoproject.com/en/stable/ref/applications/)

## Recapitulando

- Um **projeto** (`config/`) reúne configuração; um **app** (`apps/blog/`)
  reúne uma funcionalidade.
- `settings.py` é Python puro — variáveis de módulo, que tipamos e tornamos
  sensíveis a ambiente.
- Um app só existe para o Django se estiver em `INSTALLED_APPS`.
- `name` é o caminho de importação; `label` é o apelido curto das tabelas.

Agora que o esqueleto está de pé, vamos modelar os dados em
**[Modelos e o ORM](models.md)**.
