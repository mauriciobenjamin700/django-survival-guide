# Referência: autenticação e permissões

!!! quote "Pensa como criança 🧒"
    **Autenticação** é o segurança olhando seu crachá na porta: "quem é você?".
    **Autorização** (permissões) é o mesmo segurança olhando o que o crachá
    permite: "você pode entrar *nesta* sala?". O Django já vem com o segurança
    treinado — você só diz quais salas exigem qual crachá.

## Caso de uso

Só usuários logados criam posts; só o autor edita o dele. Você não escreve login,
hash de senha nem sessão — usa o que vem pronto e protege as views com um mixin:

```python
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, UpdateView


class PostCreateView(LoginRequiredMixin, CreateView):
    """Only logged-in users can create."""
    model = Post
    fields = ["title", "body"]


class PostUpdateView(UserPassesTestMixin, UpdateView):
    """Only the author can edit."""
    model = Post
    fields = ["title", "body"]

    def test_func(self) -> bool:
        return self.get_object().author.user == self.request.user
```

Vamos ao sistema inteiro.

## Possibilidades

### O que vem pronto

| Peça | O que faz |
| --- | --- |
| Modelo `User` | Usuário com username, email, senha (hasheada), flags |
| `AuthenticationMiddleware` | Coloca `request.user` em toda requisição |
| `LoginView` / `LogoutView` | Telas de login/logout prontas |
| `PasswordChangeView` / `PasswordResetView` | Troca/redefinição de senha |
| Hash de senha | Senhas nunca em texto puro |
| Permissões e grupos | Autorização por modelo |

### `request.user`: quem está na porta

```python
if request.user.is_authenticated:
    print(request.user.username)      # usuário real
else:
    ...                                # AnonymousUser (visitante)
```

| Atributo | Vale |
| --- | --- |
| `is_authenticated` | `True` para usuário logado, `False` para anônimo |
| `is_staff` | Pode entrar no admin |
| `is_superuser` | Tem **todas** as permissões |
| `is_active` | Conta ativa |

!!! info "Anônimo também é um usuário"
    Quem não logou é um `AnonymousUser` — por isso `request.user` nunca é `None`,
    e `request.user.is_authenticated` é sempre seguro de checar.

### Login, logout, senha (views prontas)

```python
# config/urls.py
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("senha/", auth_views.PasswordChangeView.as_view(), name="password_change"),
]
```

Configure os destinos no settings:

```python
LOGIN_URL = "login"                      # para onde mandar quem não logou
LOGIN_REDIRECT_URL = "blog:post-list"    # para onde ir após logar
LOGOUT_REDIRECT_URL = "blog:post-list"   # para onde ir após deslogar
```

### Proteger views

=== "Classe (CBV) — mixin"

    ```python
    from django.contrib.auth.mixins import (
        LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin,
    )

    class SecretView(LoginRequiredMixin, DetailView): ...
    class ExportView(PermissionRequiredMixin, View):
        permission_required = "blog.can_export"
    ```

=== "Função — decorador"

    ```python
    from django.contrib.auth.decorators import login_required, permission_required

    @login_required
    def minha(request): ...

    @permission_required("blog.add_post")
    def outra(request): ...
    ```

| Mixin (CBV) | Decorador (função) | Exige |
| --- | --- | --- |
| `LoginRequiredMixin` | `@login_required` | Estar logado |
| `PermissionRequiredMixin` | `@permission_required("app.perm")` | Uma permissão |
| `UserPassesTestMixin` | `@user_passes_test(fn)` | Passar num teste |

!!! danger "Mixin sempre PRIMEIRO na herança"
    `class V(LoginRequiredMixin, DetailView)` — o mixin à esquerda intercepta
    antes. Invertido, o gate não roda. (Ver [views CBV](views-cbv.md) sobre MRO.)

### Permissões: as quatro automáticas + as suas

Todo modelo ganha 4 permissões automáticas: `add`, `change`, `delete`, `view`. O
nome completo é `app_label.action_modelo`:

```python
request.user.has_perm("blog.add_post")
request.user.has_perm("blog.delete_comment")
```

Permissões extras, na `Meta` do modelo:

```python
class Report(models.Model):
    class Meta:
        permissions = [
            ("can_export", "Pode exportar relatórios"),
        ]
# uso: request.user.has_perm("blog.can_export")
```

### Grupos: crachás em lote

Pensa como criança: um **grupo** é uma caixinha de crachás. Em vez de dar 10
permissões a cada pessoa, você cria o grupo "Editores" com essas permissões e
só coloca as pessoas na caixinha.

```python
from django.contrib.auth.models import Group, Permission

editores = Group.objects.create(name="Editores")
editores.permissions.add(Permission.objects.get(codename="add_post"))
user.groups.add(editores)        # herda todas as permissões do grupo
```

### Hash de senha

```python
from django.contrib.auth import get_user_model, authenticate

User = get_user_model()
user = User.objects.create_user("ana", password="segredo123")  # já hasheia

user.check_password("segredo123")   # True
user.check_password("errado")        # False

# autenticar (checa credenciais)
u = authenticate(username="ana", password="segredo123")   # user ou None
```

!!! danger "Nunca guarde nem compare senha crua"
    `create_user`/`set_password` hasheiam; `check_password` compara com
    segurança. Jamais faça `User(password="...")` direto — isso salva texto puro.

### Usuário customizado (faça cedo!)

```python
# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """Project user with extra fields."""
    bio = models.TextField(blank=True)
```

```python
# settings.py
AUTH_USER_MODEL = "accounts.User"
```

!!! warning "Troque o `User` no início do projeto"
    Mudar `AUTH_USER_MODEL` depois que o banco existe é doloroso (migrações
    complicadas). Se há **qualquer** chance de precisar de campos extras no
    usuário, crie o modelo customizado já na primeira migração. E sempre
    referencie via `settings.AUTH_USER_MODEL` (models) ou `get_user_model()`
    (código).

## Recap

- Autenticação = "quem é você"; permissões = "o que você pode".
- `request.user` sempre existe (`AnonymousUser` para visitante);
  `is_authenticated`/`is_staff`/`is_superuser`.
- Login/logout/senha são views prontas; configure os `*_URL` no settings.
- Proteja: mixin (CBV, sempre 1º) ou decorador (função) —
  `LoginRequired`/`PermissionRequired`/`UserPassesTest`.
- 4 permissões automáticas por modelo + extras na `Meta`; **grupos** dão
  permissões em lote.
- Senhas sempre hasheadas (`create_user`/`check_password`). Troque o `User` por
  um customizado **no começo** e use `get_user_model()`.

Você agora tem a referência das camadas principais do Django. 🎉 Volte ao
[Tutorial](../tutorial/project-setup.md) para vê-las juntas, ou explore qualquer
página de referência à vontade.
