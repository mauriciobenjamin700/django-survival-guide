# Referência: settings

!!! quote "Pensa como criança 🧒"
    O `settings.py` é o **painel de botões** de todo o projeto: onde fica o banco,
    quais "peças" (apps) estão ligadas, se o modo de teste está aceso. Não tem
    mágica — é só um arquivo Python com variáveis. Quando o Django acorda, ele lê
    esse painel e se configura.

## Caso de uso

Você quer o mesmo código rodando em dois lugares: no seu PC (banco simples, erros
detalhados) e em produção (banco real, seguro). A solução é ler os valores
sensíveis do **ambiente**, com padrões amigáveis para o dev:

```python
# config/settings.py
import os
from pathlib import Path

BASE_DIR: Path = Path(__file__).resolve().parent.parent

SECRET_KEY: str = os.environ.get("DJANGO_SECRET_KEY", "dev-only-change-me")
DEBUG: bool = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS: list[str] = os.environ.get(
    "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1"
).split(",")
```

No PC, roda sem configurar nada. Em produção, você define as variáveis de
ambiente e nada no código muda. Vamos ao painel completo.

## Possibilidades

### Os settings que você mais toca

| Setting | O que controla |
| --- | --- |
| `SECRET_KEY` | Chave secreta (assinaturas, sessões). Segredo absoluto |
| `DEBUG` | `True` mostra erros detalhados. **Sempre `False` em produção** |
| `ALLOWED_HOSTS` | Domínios que podem servir o site |
| `INSTALLED_APPS` | Apps ligados (seus + do Django + de terceiros) |
| `MIDDLEWARE` | Camadas que envolvem cada requisição (ordem importa!) |
| `DATABASES` | Conexão(ões) com o banco |
| `TEMPLATES` | Onde e como achar templates |
| `STATIC_URL` / `STATIC_ROOT` | Arquivos estáticos (CSS/JS/imagens) |
| `MEDIA_URL` / `MEDIA_ROOT` | Arquivos enviados por usuários |
| `LANGUAGE_CODE` / `TIME_ZONE` | Idioma e fuso |
| `USE_I18N` / `USE_TZ` | Traduções ligadas / datas com fuso |
| `DEFAULT_AUTO_FIELD` | Tipo da PK automática |
| `AUTH_USER_MODEL` | Modelo de usuário do projeto |
| `LOGIN_URL` / `LOGIN_REDIRECT_URL` | Rotas de login |

!!! danger "O tripé de segurança: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`"
    Em produção: `SECRET_KEY` vem do ambiente (nunca no Git), `DEBUG=False`
    (senão você vaza stack traces com dados sensíveis), e `ALLOWED_HOSTS` lista
    só seus domínios. Rode `python manage.py check --deploy` para ele apontar o
    que falta.

### `DATABASES`: dev × produção

```python
# desenvolvimento: SQLite (um arquivo, zero configuração)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# produção: PostgreSQL via ambiente
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["DB_NAME"],
        "USER": os.environ["DB_USER"],
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}
```

### `MIDDLEWARE`: a ordem é uma cebola

Pensa como criança: cada middleware é uma **casca de cebola** em volta da view. A
requisição entra atravessando as cascas de fora para dentro; a resposta sai de
dentro para fora. Trocar a ordem muda o comportamento.

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",   # dá o request.user
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

!!! warning "Não reordene sem saber"
    `AuthenticationMiddleware` precisa vir **depois** de `SessionMiddleware`
    (ele lê a sessão para achar o usuário). A ordem padrão do `startproject` é
    correta — só mexa com motivo.

### Padrões de organização

Como o `settings.py` cresce, há três abordagens comuns:

=== "Um arquivo + ambiente (o do exemplo)"

    Um `settings.py` só, lendo o que varia de `os.environ`. Simples e suficiente
    para a maioria dos projetos.

=== "Pacote `settings/` por ambiente"

    ```text
    config/settings/
    ├── base.py        # comum
    ├── dev.py         # from .base import *  (+ overrides)
    └── prod.py        # from .base import *  (+ overrides)
    ```
    Escolhe-se via `DJANGO_SETTINGS_MODULE=config.settings.prod`.

=== "Biblioteca (django-environ)"

    Lê um arquivo `.env` e converte tipos (`env.bool`, `env.db`). Reduz o
    boilerplate de `os.environ`.

!!! tip "Tipar os settings ajuda"
    Anotar `DEBUG: bool`, `ALLOWED_HOSTS: list[str]` não muda o comportamento,
    mas documenta o formato esperado e o editor te acompanha. É o nosso princípio
    de tipagem clara até na configuração.

### `manage.py` e `DJANGO_SETTINGS_MODULE`

O Django descobre qual settings usar pela variável de ambiente
`DJANGO_SETTINGS_MODULE`. O `manage.py` a define para você em desenvolvimento:

```python
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
```

Em produção, o servidor (Gunicorn/Uvicorn) a define apontando para o módulo de
produção.

## Recap

- `settings.py` é Python puro — variáveis que o Django lê ao iniciar.
- Leia o que varia do **ambiente** (`os.environ`) com padrões de dev; o mesmo
  código roda em qualquer lugar.
- Tripé de segurança: `SECRET_KEY` (do ambiente), `DEBUG=False` em produção,
  `ALLOWED_HOSTS` restrito. Valide com `check --deploy`.
- `DATABASES` troca SQLite (dev) por PostgreSQL (prod); `MIDDLEWARE` é uma cebola
  onde a ordem importa.
- Organize com um arquivo + env, um pacote por ambiente, ou `django-environ`.

Um dos apps mais importantes vem ligado por padrão: o de usuários. Veja
**[autenticação e permissões](auth.md)**.
