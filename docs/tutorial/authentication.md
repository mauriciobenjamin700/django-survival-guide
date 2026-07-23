# Autenticação

O Django já vem com um **sistema de autenticação** completo: modelo de usuário,
login/logout, sessões, senhas com hash e controle de permissões. Você raramente
precisa escrever isso do zero.

!!! quote "O que você ganha pronto"
    - Um modelo `User` (`django.contrib.auth`).
    - Views de login/logout.
    - Hash seguro de senhas (nunca em texto puro).
    - `request.user` disponível em toda view.
    - Mixins e decoradores para proteger páginas.

## Usuário logado: `request.user`

Graças ao `AuthenticationMiddleware`, toda requisição carrega o usuário atual:

```python
if request.user.is_authenticated:
    print(request.user.username)
else:
    print("visitante anônimo")
```

No template, o mesmo objeto está disponível como `user`:

```django
{% if user.is_authenticated %}
  <a href="{% url 'blog:post-create' %}">New post</a>
  <a href="{% url 'logout' %}">Logout ({{ user.username }})</a>
{% else %}
  <a href="{% url 'login' %}">Login</a>
{% endif %}
```

## Login e logout: views prontas

Não escrevemos essas views — usamos as do próprio Django, só apontando as rotas:

```python
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
```

A `LoginView` procura um template em `registration/login.html`. O nosso:

```django title="templates/registration/login.html"
{% extends "base.html" %}
{% block content %}
  <h1>Login</h1>
  <form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Login</button>
  </form>
{% endblock %}
```

E configuramos para onde ir em cada caso, no `settings.py`:

```python
LOGIN_URL: str = "login"                       # (1)!
LOGIN_REDIRECT_URL: str = "blog:post-list"     # (2)!
LOGOUT_REDIRECT_URL: str = "blog:post-list"    # (3)!
```

1. Para onde mandar quem tenta acessar página protegida sem login.
2. Para onde ir depois de logar com sucesso.
3. Para onde ir depois de deslogar.

## Protegendo views: `LoginRequiredMixin`

Como usamos views baseadas em classe, protegemos com um **mixin** — composição,
sem tocar na lógica da view:

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView


class PostCreateView(LoginRequiredMixin, CreateView):
    """Only logged-in users can create posts."""
    # ...
```

Quem não estiver logado é redirecionado para `LOGIN_URL`, com o destino original
preservado no parâmetro `?next=`, para voltar após o login.

!!! warning "O mixin vem primeiro"
    Sempre `class MinhaView(LoginRequiredMixin, GenericView)`. Se inverter, o
    mixin não intercepta a requisição a tempo. A ordem da esquerda para a direita
    define a cadeia de herança (MRO).

!!! info "Views de função? Use o decorador"
    O equivalente para views de função é `@login_required`:
    ```python
    from django.contrib.auth.decorators import login_required

    @login_required
    def minha_view(request): ...
    ```
    Mixin para classes, decorador para funções — mesma ideia.

## Senhas: nunca em texto puro

O Django faz **hash** das senhas automaticamente. Você nunca armazena nem compara
a senha crua:

```python
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.create_user(username="ana", password="segredo123")
# a senha é hasheada antes de ir ao banco

user.check_password("segredo123")  # -> True
user.check_password("errado")       # -> False
```

Os validadores em `AUTH_PASSWORD_VALIDATORS` (comprimento mínimo, senhas comuns,
etc.) reforçam senhas fortes no cadastro.

!!! tip "`get_user_model()` em vez de importar `User`"
    Sempre referencie o usuário via `settings.AUTH_USER_MODEL` (nos modelos) ou
    `get_user_model()` (no código). Assim, se o projeto trocar por um usuário
    customizado, nada quebra. Foi o que fizemos no modelo `Author`.

## Permissões e grupos (visão geral)

Além de "logado ou não", o Django tem **permissões** por modelo
(`add`, `change`, `delete`, `view`) e **grupos** que agrupam permissões. Para
gating por permissão em CBVs, há o `PermissionRequiredMixin`:

```python
from django.contrib.auth.mixins import PermissionRequiredMixin


class PostDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = "blog.delete_post"
```

!!! quote "📖 Na documentação oficial"
    - [Using the authentication system](https://docs.djangoproject.com/en/stable/topics/auth/default/)

## Recapitulando

- Autenticação vem pronta: `User`, login/logout, sessões, hash de senha.
- `request.user` / `user` no template dizem quem está logado.
- Aponte rotas para `LoginView`/`LogoutView` e configure os `*_URL` no settings.
- Proteja CBVs com `LoginRequiredMixin` (sempre primeiro na herança).
- Senhas são hasheadas; use `create_user`/`check_password` e `get_user_model()`.

Você concluiu o **Tutorial**! Tem um blog completo, tipado e orientado a objetos.
Agora vamos expor esses mesmos dados como uma **[API REST com DRF](../advanced/drf.md)**.
