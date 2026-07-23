# Configuracao, ambientes e segredos (12-factor)

!!! quote "Pensa como criança 🧒"
    A receita do bolo é sempre a mesma (o **código**). Mas a quantidade de açúcar
    muda: na sua casa você põe bastante, na casa da vovó diabética você põe zero.
    O **ambiente** é a cozinha onde o bolo é feito, e os **segredos** são os
    ingredientes secretos que você nunca escreve num papel que qualquer um lê. A
    receita fica no caderno (Git); o açúcar e o ingrediente secreto ficam na
    cozinha (variáveis de ambiente).

## Caso de uso

Você tem um `settings.py` e, sem pensar, escreveu isto:

```python
SECRET_KEY = "django-insecure-l9$k2m..."
DEBUG = True
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "blog",
        "USER": "postgres",
        "PASSWORD": "supersenha123",
        "HOST": "localhost",
    }
}
```

Aí você deu `git push`. Pronto: sua senha do banco e sua `SECRET_KEY` estão no
histórico do repositório **para sempre**, e o `DEBUG = True` vai para produção
mostrando stack traces para o mundo. O jeito certo é ler tudo isso do
**ambiente**:

```python
import os

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["DB_NAME"],
        "USER": os.environ["DB_USER"],
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": os.environ.get("DB_HOST", "localhost"),
    }
}
```

O código não conhece mais nenhuma senha. Ele só sabe "leia `DB_PASSWORD` de onde
você estiver rodando". Isto é o **[12-factor](https://12factor.net/config)**:
**config vive no ambiente, não no código.**

## Possibilidades

### Por que separar config do código?

O manifesto 12-factor tem uma regra de ouro (Factor III): você deveria poder
tornar seu repositório **público agora mesmo** sem vazar nenhum segredo. Se não
pode, é porque tem config escondida no código.

| Vai no Git (código) | NÃO vai no Git (ambiente) |
| --- | --- |
| Estrutura de `INSTALLED_APPS`, middleware, `ROOT_URLCONF` | `SECRET_KEY` |
| Nomes lógicos ("existe um banco `default`") | Senha, usuário e host do banco |
| Defaults seguros (`DEBUG = False`) | Chaves de API (Stripe, AWS, e-mail) |
| `.env.example` (só os nomes das variáveis) | `.env` (os valores reais) |

!!! danger "Nunca comite `SECRET_KEY`, senhas ou o arquivo `.env`"
    Se um segredo já foi comitado, trocar o valor não basta: ele continua no
    histórico. Você precisa **rotacionar** (gerar um novo segredo) e revogar o
    antigo. Prevenir é muito mais barato: adicione `.env` ao `.gitignore` no
    primeiro dia.

### Lendo variáveis: `os.environ` puro

O jeito mais simples, sem dependência nenhuma. O detalhe importante é a
diferença entre `[]` e `.get()`:

```python
import os

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]        # (1)!
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"  # (2)!
```

1. `os.environ["X"]` **explode** com `KeyError` se a variável não existir. Use
    para segredos obrigatórios: melhor o app não subir do que subir inseguro.
2. `os.environ.get("X", default)` retorna o default se faltar. Use para config
    opcional.

!!! warning "Variável de ambiente é sempre string"
    `os.environ` só entrega texto. `DEBUG=True` no shell vira a string
    `"True"`, e a string `"False"` é **verdadeira** em Python (qualquer string
    não vazia é truthy). Por isso comparamos com `== "True"`. Para números use
    `int(os.environ["PORT"])`. É aqui que uma biblioteca de casting ajuda.

### Lendo variáveis: `django-environ` (recomendado)

`django-environ` resolve o casting de tipos e ainda entende URLs de banco. É a
opção que a maioria dos projetos Django usa.

```bash
uv add django-environ
```

```python
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),          # (1)!
    ALLOWED_HOSTS=(list, ["127.0.0.1"]),
)
environ.Env.read_env(BASE_DIR / ".env")  # (2)!

SECRET_KEY = env("DJANGO_SECRET_KEY")            # obrigatório: sem default
DEBUG = env("DJANGO_DEBUG")                      # já vira bool de verdade
ALLOWED_HOSTS = env("ALLOWED_HOSTS")             # já vira lista

DATABASES = {
    "default": env.db("DATABASE_URL"),           # (3)!
}
```

1. Você declara o **tipo** e o **default** de cada variável uma vez. Aí `env("X")`
    já devolve o tipo certo (bool, int, list...), sem `== "True"` na mão.
2. `read_env()` carrega o arquivo `.env` para dentro de `os.environ`. Em produção
    você normalmente **não** tem `.env`: as variáveis já vêm do ambiente real, e
    essa linha simplesmente não encontra o arquivo e segue em frente.
3. `env.db()` faz o parse de uma URL como
    `postgres://user:senha@host:5432/blog` no dicionário que o Django espera.
    Uma variável só, em vez de cinco.

| Método | Lê | Exemplo de valor |
| --- | --- | --- |
| `env("X")` | string | `abc` |
| `env.bool("X")` | booleano | `True` / `False` |
| `env.int("X")` | inteiro | `5432` |
| `env.list("X")` | lista (separada por vírgula) | `a,b,c` |
| `env.db("DATABASE_URL")` | dict de conexão de banco | `postgres://...` |
| `env.cache("CACHE_URL")` | dict de cache | `redis://...` |

### O par `.env` + `.env.example`

Dois arquivos que andam juntos:

- **`.env`** — os valores **reais** (com segredos). Fica no `.gitignore`, nunca
  no Git. Cada dev/servidor tem o seu.
- **`.env.example`** — só os **nomes** das variáveis, com valores fake ou vazios.
  **Vai** no Git. É a documentação de "o que preciso configurar para rodar".

`.env` (na sua máquina, secreto):

```bash
DJANGO_SECRET_KEY=uma-chave-longa-e-aleatoria-de-verdade
DJANGO_DEBUG=True
DATABASE_URL=postgres://postgres:supersenha123@localhost:5432/blog
ALLOWED_HOSTS=127.0.0.1,localhost
```

`.env.example` (vai para o Git, sem segredos):

```bash
DJANGO_SECRET_KEY=
DJANGO_DEBUG=False
DATABASE_URL=postgres://user:password@localhost:5432/dbname
ALLOWED_HOSTS=127.0.0.1,localhost
```

`.gitignore`:

```bash
.env
*.env
!.env.example
```

!!! tip "Gerando uma `SECRET_KEY` nova"
    Nunca reaproveite a chave que o `startproject` gerou (ela tem o prefixo
    `django-insecure-` de propósito). Gere uma para produção:
    ```bash
    python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
    ```
    Cole o resultado no `.env` do servidor, nunca no código.

### Escolhendo settings: `DJANGO_SETTINGS_MODULE`

O Django precisa saber **qual** módulo de settings usar. Isso vem da variável de
ambiente `DJANGO_SETTINGS_MODULE`, que o `manage.py` e o `wsgi.py`/`asgi.py`
definem com um default:

```python
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
```

`setdefault` só define se ainda não existir — então em produção você
**sobrescreve** exportando outra:

```bash
export DJANGO_SETTINGS_MODULE=config.settings.prod
python manage.py migrate
```

Existem duas estratégias para lidar com múltiplos ambientes. Escolha uma:

### Estratégia A: arquivo único guiado por env

Um `settings.py` só, e os `if` decidem pelo ambiente. Simples, ótimo para
projetos pequenos e médios.

```python
import environ

env = environ.Env(DJANGO_DEBUG=(bool, False))

DEBUG = env("DJANGO_DEBUG")

if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

- **Prós:** um arquivo, fácil de seguir, nada de import mágico.
- **Contras:** pode virar uma sopa de `if` se os ambientes divergirem muito.

### Estratégia B: settings divididos (split settings)

Vire `settings.py` num **pacote** `settings/` com uma parte comum e uma por
ambiente:

```text
config/
└── settings/
    ├── __init__.py
    ├── base.py      # tudo que é comum
    ├── dev.py       # from .base import *  (+ ajustes de dev)
    ├── prod.py      # from .base import *  (+ ajustes de prod)
    └── test.py      # from .base import *  (+ ajustes de teste)
```

`base.py` (o tronco comum):

```python
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.blog",
]

ROOT_URLCONF = "config.urls"
```

`dev.py` (herda tudo e ajusta):

```python
from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

`prod.py` (herda tudo e endurece):

```python
from .base import *  # noqa: F403

DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")  # noqa: F405

DATABASES = {"default": env.db("DATABASE_URL")}  # noqa: F405

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

E você seleciona o ambiente pela variável:

```bash
export DJANGO_SETTINGS_MODULE=config.settings.prod
```

!!! note "`from .base import *` é a exceção à regra dos imports"
    Em código de aplicação evitamos `import *`. Em split settings ele é o
    **padrão idiomático**: settings são só variáveis de módulo, e o objetivo é
    justamente puxar todas de `base` para dentro do arquivo do ambiente. Os
    `# noqa` calam o linter, que reclamaria de nomes "não definidos" vindos do
    `*`.

```mermaid
flowchart TD
    ENV["DJANGO_SETTINGS_MODULE"] -->|config.settings.dev| DEV["dev.py"]
    ENV -->|config.settings.prod| PROD["prod.py"]
    ENV -->|config.settings.test| TEST["test.py"]
    DEV --> BASE["base.py<br/>(config comum)"]
    PROD --> BASE
    TEST --> BASE
```

!!! tip "Estratégia A vs. B — qual escolher?"
    Comece na **A** (arquivo único + env). Migre para **B** quando os ambientes
    começarem a divergir de verdade (backends diferentes, apps só de dev como
    `debug_toolbar`, etc.). Não existe "certo" universal — existe o que mantém o
    `settings` legível para o seu tamanho de projeto.

### Dependências por ambiente

Assim como a config, as **dependências** mudam por ambiente: `pytest` e
`django-debug-toolbar` não têm por que ir para produção. Com `uv` você usa
grupos de dependências:

```bash
uv add django django-environ psycopg          # roda em produção
uv add --group dev pytest-django ruff django-debug-toolbar  # só desenvolvimento
```

Isso grava no `pyproject.toml`:

```toml
[project]
dependencies = [
    "django>=6.0",
    "django-environ>=0.11",
    "psycopg>=3.2",
]

[dependency-groups]
dev = [
    "pytest-django>=4.9",
    "ruff>=0.9",
    "django-debug-toolbar>=4.4",
]
```

No servidor você instala **só** o que produção precisa:

```bash
uv sync --no-dev
```

!!! info "`debug_toolbar` só entra em dev"
    Apps que só existem em desenvolvimento devem entrar no `INSTALLED_APPS`
    apenas no `dev.py` (ou dentro de um `if DEBUG:` na estratégia A). Colocá-los
    no `base.py` faria produção tentar importar um pacote que você nem instalou
    com `--no-dev`.

### Estrutura de projeto que escala: pasta `apps/`

Quando o projeto cresce, jogar todo app na raiz vira bagunça. Agrupe os apps
numa pasta `apps/`, cada um com **uma responsabilidade**:

```text
myproject/
├── manage.py
├── pyproject.toml
├── .env.example
├── .gitignore
├── config/                 # o "projeto" Django (settings, urls, wsgi)
│   ├── __init__.py
│   ├── settings/
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
└── apps/                   # seus apps de domínio
    ├── __init__.py
    ├── blog/
    │   ├── __init__.py
    │   ├── apps.py
    │   ├── models.py
    │   ├── views.py
    │   └── urls.py
    └── accounts/
        └── ...
```

Para o Django achar `apps.blog`, referencie com o caminho completo no
`INSTALLED_APPS` e no `AppConfig`:

```python
# apps/blog/apps.py
from django.apps import AppConfig


class BlogConfig(AppConfig):
    """Configuration for the blog app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.blog"
```

```python
# config/settings/base.py
INSTALLED_APPS = [
    "django.contrib.admin",
    # ...
    "apps.blog",
    "apps.accounts",
]
```

!!! tip "Um app, uma responsabilidade"
    Pergunte "eu conseguiria arrancar esse app e usar em outro projeto?". `blog`,
    `accounts`, `payments` são bons apps: coesos e focados. Um app gigante
    chamado `core` que faz tudo é o cheiro contrário. Apps pequenos e
    reutilizáveis são o coração da filosofia do Django.

!!! quote "📖 Na documentação oficial"
    - [Django settings](https://docs.djangoproject.com/en/6.0/topics/settings/)
    - [django-environ](https://django-environ.readthedocs.io/)
    - [The Twelve-Factor App — Config](https://12factor.net/config)

## Recap

- **Config vive no ambiente, não no código** (12-factor): você deveria poder
  tornar o repo público sem vazar nada.
- Nunca comite `SECRET_KEY`, senhas nem `.env`. Se vazou, **rotacione** — trocar
  o valor não apaga o histórico.
- Leia variáveis com `os.environ` (lembre: tudo é string) ou, melhor, com
  `django-environ` (casting de tipos + `env.db()` de brinde).
- `.env` (valores reais, no `.gitignore`) anda junto com `.env.example` (só os
  nomes, no Git).
- `DJANGO_SETTINGS_MODULE` escolhe o módulo de settings; `setdefault` no
  `manage.py`, `export` em produção.
- Dois padrões: **arquivo único guiado por env** (comece aqui) ou **split
  settings** (`base`/`dev`/`prod`/`test` com `from .base import *`).
- Dependências por ambiente com grupos do `uv` (`--group dev`); em produção,
  `uv sync --no-dev`.
- Escale com uma pasta `apps/`, um app por responsabilidade.

Quer ver cada chave de settings em detalhe? Vá para a
**[referência de settings](settings.md)**.
