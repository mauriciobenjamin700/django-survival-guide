# django-allauth

O Django traz login por usuário/senha. Mas cadastro com **verificação de
e-mail**, **login social** (Google, GitHub) e recuperação de conta dá trabalho
para fazer certo. O `django-allauth` entrega isso pronto.

!!! quote "Pensa como criança 🧒"
    O portão do prédio já abre com a sua chave (o login do Django). O allauth é o
    **porteiro completo**: além da chave, ele aceita seu crachá do trabalho (login
    social), confere se você é você mesmo por e-mail, e cuida de "esqueci a senha".

## Instalação e configuração

```bash
uv add "django-allauth[socialaccount]"
```

```python
# settings.py
INSTALLED_APPS = [
    "django.contrib.sites",              # (1)!
    "allauth",
    "allauth.account",
    "allauth.socialaccount",             # login social (opcional)
    "allauth.socialaccount.providers.google",   # um provedor
    # ...
]

MIDDLEWARE = [
    # ...
    "allauth.account.middleware.AccountMiddleware",   # (2)!
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",       # login normal do admin
    "allauth.account.auth_backends.AuthenticationBackend",  # login do allauth
]

SITE_ID = 1
```

1. O allauth depende do framework `sites`. `SITE_ID = 1` aponta para o site
    padrão.
2. O `AccountMiddleware` é **obrigatório** nas versões atuais — esquecer causa
    erro no primeiro acesso.

```python
# urls.py
urlpatterns = [
    path("accounts/", include("allauth.urls")),   # login, signup, reset, social
]
```

```bash
python manage.py migrate
```

Pronto: `/accounts/login/`, `/accounts/signup/`, `/accounts/password/reset/` já
funcionam.

## Possibilidades

### Configurar o comportamento da conta

Várias opções foram renomeadas/reestruturadas nas versões recentes (continuam
sendo settings `ACCOUNT_*` separados, não um dicionário único):

```python
# settings.py
ACCOUNT_LOGIN_METHODS = {"email"}            # logar por e-mail (não username)
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "mandatory"     # exige verificar o e-mail
ACCOUNT_EMAIL_REQUIRED = True
```

| Opção | O que controla |
| --- | --- |
| `ACCOUNT_LOGIN_METHODS` | Logar por `email`, `username` ou ambos |
| `ACCOUNT_EMAIL_VERIFICATION` | `"mandatory"`, `"optional"` ou `"none"` |
| `ACCOUNT_SIGNUP_FIELDS` | Campos do cadastro (`*` = obrigatório) |
| `ACCOUNT_RATE_LIMITS` | Limites de tentativa (anti força-bruta) |

!!! warning "As chaves de settings do allauth mudam entre versões"
    Versões maiores renomearam settings (ex.: `ACCOUNT_AUTHENTICATION_METHOD` →
    `ACCOUNT_LOGIN_METHODS`). Sempre confira a doc **da versão que você instalou**
    — copiar tutorial antigo gera erro silencioso de configuração.

### Login social (ex.: Google)

Pensa como criança: o botão "Entrar com Google" é um combinado de confiança —
o Google confirma quem você é e o allauth cria/associa a conta.

1. Registre o app no console do provedor (Google Cloud) e pegue `client_id` +
   `secret`.
2. Configure no `settings.py` **ou** cadastre no admin (modelo *Social
   application*):

```python
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": os.environ["GOOGLE_CLIENT_ID"],
            "secret": os.environ["GOOGLE_SECRET"],
        },
        "SCOPE": ["profile", "email"],
    }
}
```

3. O botão de login aparece em `/accounts/login/`.

!!! danger "Segredos do provedor vêm do ambiente"
    `client_id` e `secret` são credenciais — leia de variáveis de ambiente, nunca
    fixe no código versionado. Ver [settings](../referencia/settings.md).

### Personalizar os templates

O allauth traz templates prontos, mas feios. Sobrescreva criando arquivos com o
mesmo caminho em `templates/account/` (ex.: `templates/account/login.html`) — o
Django acha o seu primeiro. Estenda seu `base.html` para manter a identidade.

## Quando usar (e quando não)

!!! tip "Use allauth quando..."
    Você precisa de **login social**, **verificação de e-mail** robusta, ou fluxo
    de conta completo. Fazer isso na mão é fácil de errar (segurança).

!!! warning "Talvez não precise se..."
    O projeto é uma API pura para um app mobile/SPA — aí o fluxo é por **token/JWT**
    (veja [afins](afins.md) → `djangorestframework-simplejwt`), e o allauth tem o
    `allauth.headless` para esse caso, mas avalie se um JWT simples já resolve.

## Recapitulando

- allauth entrega cadastro, verificação de e-mail, recuperação e **login social**.
- Ritual: `uv add` → apps (`sites` + `allauth.*`) → `AccountMiddleware` →
  `AUTHENTICATION_BACKENDS` → `SITE_ID` → `include("allauth.urls")` → `migrate`.
- Comportamento via settings `ACCOUNT_*`/`SOCIALACCOUNT_*` (nomes mudam entre
  versões — confira a doc da sua).
- Segredos de provedor no ambiente; personalize sobrescrevendo `templates/account/`.

!!! quote "📖 Na documentação oficial"
    - [django-allauth](https://docs.allauth.org/)

Login resolvido. E tarefas pesadas que não cabem no request?
**[Celery](celery.md)**.
