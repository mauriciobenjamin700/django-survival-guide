# Configurando o projeto

!!! info "Ponto de partida"
    Esta página continua de onde a **[Instalação](../get-started/installation.md)**
    parou: você já tem uma pasta com `manage.py`, `config/` e o servidor
    subindo. Se ainda não tem, faça aquela página antes — leva poucos minutos.

Antes de escrever qualquer funcionalidade, precisamos entender **como um projeto
Django é organizado**. Django separa dois conceitos:

- **Projeto** — a configuração geral (settings, URLs raiz, WSGI/ASGI).
- **App** — um módulo com uma responsabilidade (aqui, o `blog`).

Um projeto contém vários apps. Cada app deve fazer *uma* coisa bem feita.

## A estrutura que vamos montar

```text
meu-blog/                     # (no repositório do guia: example/)
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

## Criando o app `blog`

O `config/` você já criou na Instalação (`django-admin startproject config .`).
Agora crie o app, na sua pasta de projeto:

```bash
mkdir -p apps/blog
touch apps/__init__.py
uv run python manage.py startapp blog apps/blog
```

Linha por linha:

1. `mkdir -p apps/blog` — o `startapp` **não cria** a pasta de destino, ela
   precisa existir antes.
2. `touch apps/__init__.py` — transforma `apps/` em um **pacote Python**
   explícito.
3. `startapp blog apps/blog` — gera o esqueleto do app *dentro* de `apps/blog`.

??? info "O `__init__.py` é mesmo obrigatório?"
    Tecnicamente não: desde o Python 3.3 existem *namespace packages*, e o
    `import apps.blog` funciona mesmo sem o arquivo. Criamos assim mesmo porque
    o pacote explícito deixa a intenção clara e evita comportamentos estranhos
    em ferramentas de build, empacotamento e descoberta de testes.

!!! warning "Windows"
    `mkdir -p` e `touch` são comandos Unix. No PowerShell:
    ```powershell
    mkdir apps\blog
    New-Item apps\__init__.py
    uv run python manage.py startapp blog apps\blog
    ```

O resultado:

```text
apps/
├── __init__.py
└── blog/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── migrations/
    ├── models.py
    ├── tests.py
    └── views.py
```

!!! note "Faltam `urls.py`, `forms.py` e `templates/`?"
    Faltam mesmo — o `startapp` não gera esses. Você cria cada um quando a
    página do tutorial correspondente precisar dele. Nada de arquivo vazio
    sobrando.

## O `settings.py` — sem mágica

O `settings.py` é só um **módulo Python com variáveis de nível de módulo** que o
Django lê ao iniciar. Nada de formato especial.

Abra `config/settings.py`. O `startproject` deixou a `SECRET_KEY` fixa no código
e o `DEBUG = True` cravado. Troque essas linhas para lerem do ambiente, com
padrões amigáveis para desenvolvimento:

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

!!! note "Aspas simples no arquivo gerado"
    O `startproject` escreve tudo com aspas simples (`'django.contrib.admin'`).
    Neste guia padronizamos **aspas duplas** — é só estilo, o Python trata os
    dois iguais. Se quiser normalizar o arquivo inteiro de uma vez, o
    [ruff](../sobre/lint.md) faz isso com `ruff format`.

!!! tip "Tipagem em settings"
    Anotar `BASE_DIR: Path`, `DEBUG: bool` etc. não muda o comportamento, mas
    documenta o tipo esperado e ajuda o editor. É o nosso princípio de *tipagem
    clara* aplicado até na configuração.

!!! warning "`SECRET_KEY` e `DEBUG` em produção"
    Nunca use a `SECRET_KEY` padrão em produção, e sempre rode com `DEBUG=false`.
    Por isso lemos ambos de variáveis de ambiente: em produção você define
    `DJANGO_SECRET_KEY` e `DJANGO_DEBUG=false` sem tocar no código.

### Registrando o app

Para o Django "enxergar" o blog, ele entra em `INSTALLED_APPS` — ainda no
`config/settings.py`, adicione a última linha:

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

Só isso ainda não basta. O `startapp` gerou `apps/blog/apps.py` com
`name = "blog"` — que é o caminho **errado**, porque o app não está na raiz.
Edite o arquivo para declarar o caminho real e um `label` curto, para as tabelas
não ficarem com nome gigante:

```python
from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field: str = "django.db.models.BigAutoField"  # (1)!
    name: str = "apps.blog"                                    # (2)!
    label: str = "blog"                                        # (3)!
```

1. O tipo da **chave primária automática** — explicado logo abaixo.
2. O **caminho de importação** do app.
3. O **apelido interno**: as tabelas viram `blog_post`, `blog_tag`...

!!! note "`name` vs `label`"
    - `name` é o **caminho de importação** (`apps.blog`) — precisa bater com a
      pasta real.
    - `label` é o **apelido interno** usado em nomes de tabela e migrações. Sem
      ele, as tabelas seriam `apps_blog_post` em vez de `blog_post`.

### Para que serve o `default_auto_field`

Toda tabela precisa de uma **chave primária** (a coluna que identifica cada
linha, o `id`). Você quase nunca declara ela: o Django cria sozinho. Essa linha
diz **de que tipo** ele cria.

!!! quote "Pensa como criança 🧒"
    É a **senha da fila do médico**: cada pessoa que chega ganha o próximo número,
    e ninguém repete. O `default_auto_field` só escolhe **que tipo de papelzinho**
    a máquina imprime.

Com `BigAutoField` você ganha um inteiro de 64 bits que o banco incrementa a cada
`INSERT` — `1, 2, 3, ...`. Detalhes que valem saber:

- Vale para os models **deste app** que não declaram `primary_key` — e é o padrão
  que o `startapp` já escreve.
- Se você apagar a linha, o Django usa o `DEFAULT_AUTO_FIELD` do `settings.py`
  (que o `startproject` já define como `BigAutoField`). Sem nenhum dos dois, cai
  no `AutoField` de 32 bits — que estoura em ~2,1 bilhões de linhas.
- Mudar o valor **depois** que existem tabelas gera migração (`ALTER COLUMN`), e
  em tabela grande isso é lento. Decida cedo.

??? question "E se eu quiser UUID como chave primária?"
    Tentação natural: trocar essa linha por um UUID. **Não funciona** — nem com
    um campo seu:

    ```python
    class BlogConfig(AppConfig):
        default_auto_field: str = "apps.blog.fields.UUIDAutoField"
    ```

    ```text
    ValueError: Primary key 'apps.blog.fields.UUIDAutoField' referred by
    apps.blog.apps.BlogConfig.default_auto_field must subclass AutoField.
    ```

    O Django exige que o campo seja subclasse de `AutoField` (a metaclasse
    `AutoFieldMeta` só aceita `BigAutoField`, `SmallAutoField` ou subclasses
    reais) — e `UUIDField` não é. O próprio comentário no código do Django diz que
    campo automático **não-inteiro** só será possível quando o valor puder vir de
    um default do banco.

    O caminho certo é declarar a PK **no model**, normalmente num model abstrato
    para não repetir:

    ```python
    # apps/blog/models.py
    import uuid

    from django.db import models


    class BaseModel(models.Model):
        """Base abstrata com chave primária UUID."""

        id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

        class Meta:
            abstract = True


    class Post(BaseModel):
        title = models.CharField(max_length=200)
    ```

    E aí o `default_auto_field` **continua importando**: as tabelas que o Django
    cria sozinho (a intermediária de um `ManyToManyField`, por exemplo) seguem
    usando ele. Com os models acima, `blog_post` tem `id` UUID, mas
    `blog_post_tags` tem `id` inteiro — as duas coisas convivem.

    O que muda no resto do projeto se você adotar UUID: as rotas passam a usar
    `<uuid:pk>` em vez de `<int:pk>`, os `seed`/fixtures não podem mais chutar
    `id=1`, e cada FK cresce de 8 para 16 bytes.

    | | `BigAutoField` | `UUIDField` |
    | --- | --- | --- |
    | Tamanho | 8 bytes | 16 bytes (32 chars no SQLite) |
    | Quem gera | o banco, no `INSERT` | a aplicação, antes do `INSERT` |
    | Ordem | crescente por inserção | aleatória (v4) → índice fragmenta |
    | Na URL | `/posts/42/` — enumerável | `/posts/1fb72e6d-…/` — opaca |
    | Merge de bases | colide | não colide |

    !!! tip "UUIDv7 resolve a fragmentação"
        O v4 é aleatório, então cada `INSERT` cai num ponto qualquer do índice.
        O **v7** embute o timestamp no começo, voltando a ser crescente. No
        Python **3.14+** use `uuid.uuid7`; antes disso, a lib
        [`uuid6`](https://pypi.org/project/uuid6/).

    **Neste guia seguimos com `BigAutoField`** — é o padrão do Django, mais
    barato de índice e suficiente para o blog. Vá de UUID quando o id for
    exposto publicamente ou quando várias bases forem se juntar.

## O `manage.py`

É o canivete suíço do projeto. Todo comando administrativo passa por ele:

```bash
uv run python manage.py <comando>
```

Alguns que já vamos usar: `migrate`, `makemigrations`, `runserver`,
`createsuperuser`, `shell`, `test`.

## Conferindo se ficou de pé

```bash
uv run python manage.py check
```

Deve responder `System check identified no issues (0 silenced).`

!!! failure "`ImproperlyConfigured: Cannot import 'blog'`"
    Mensagem completa:
    ```text
    django.core.exceptions.ImproperlyConfigured: Cannot import 'blog'.
    Check that 'apps.blog.apps.BlogConfig.name' is correct.
    ```
    O `name` em `apps/blog/apps.py` ainda está como `"blog"` (o que o `startapp`
    gerou) em vez de `"apps.blog"`. É exatamente o ajuste da seção anterior.

!!! quote "📖 Na documentação oficial"
    - [Applications](https://docs.djangoproject.com/en/stable/ref/applications/)

## Recapitulando

- Um **projeto** (`config/`) reúne configuração; um **app** (`apps/blog/`)
  reúne uma funcionalidade.
- `settings.py` é Python puro — variáveis de módulo, que tipamos e tornamos
  sensíveis a ambiente.
- Um app só existe para o Django se estiver em `INSTALLED_APPS`.
- `name` é o caminho de importação; `label` é o apelido curto das tabelas.
- `manage.py check` é a forma rápida de validar a configuração antes de seguir.

Agora que o esqueleto está de pé, vamos modelar os dados em
**[Modelos e o ORM](models.md)**.
