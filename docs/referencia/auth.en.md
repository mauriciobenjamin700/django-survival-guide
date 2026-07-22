# Reference: authentication and permissions

!!! quote "Think like a child 🧒"
    **Authentication** is the guard looking at your badge at the door: "who are
    you?". **Authorization** (permissions) is the same guard looking at what the
    badge allows: "can you enter *this* room?". Django already comes with the guard
    trained — you just say which rooms require which badge.

## Use case

Only logged-in users create posts; only the author edits their own. You don't
write login, password hashing, or sessions — you use what comes ready and protect
the views with a mixin:

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

Let's go through the whole system.

## Possibilities

### What comes ready

| Part | What it does |
| --- | --- |
| `User` model | User with username, email, password (hashed), flags |
| `AuthenticationMiddleware` | Puts `request.user` on every request |
| `LoginView` / `LogoutView` | Ready-made login/logout screens |
| `PasswordChangeView` / `PasswordResetView` | Password change/reset |
| Password hashing | Passwords never in plain text |
| Permissions and groups | Authorization per model |

### `request.user`: who's at the door

```python
if request.user.is_authenticated:
    print(request.user.username)      # real user
else:
    ...                                # AnonymousUser (visitor)
```

| Attribute | Holds |
| --- | --- |
| `is_authenticated` | `True` for a logged-in user, `False` for anonymous |
| `is_staff` | Can enter the admin |
| `is_superuser` | Has **all** permissions |
| `is_active` | Active account |

!!! info "Anonymous is also a user"
    Someone who didn't log in is an `AnonymousUser` — that's why `request.user` is
    never `None`, and `request.user.is_authenticated` is always safe to check.

### Login, logout, password (ready-made views)

```python
# config/urls.py
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("senha/", auth_views.PasswordChangeView.as_view(), name="password_change"),
]
```

Configure the destinations in the settings:

```python
LOGIN_URL = "login"                      # where to send those who didn't log in
LOGIN_REDIRECT_URL = "blog:post-list"    # where to go after logging in
LOGOUT_REDIRECT_URL = "blog:post-list"   # where to go after logging out
```

### Protecting views

=== "Class (CBV) — mixin"

    ```python
    from django.contrib.auth.mixins import (
        LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin,
    )

    class SecretView(LoginRequiredMixin, DetailView): ...
    class ExportView(PermissionRequiredMixin, View):
        permission_required = "blog.can_export"
    ```

=== "Function — decorator"

    ```python
    from django.contrib.auth.decorators import login_required, permission_required

    @login_required
    def minha(request): ...

    @permission_required("blog.add_post")
    def outra(request): ...
    ```

| Mixin (CBV) | Decorator (function) | Requires |
| --- | --- | --- |
| `LoginRequiredMixin` | `@login_required` | Being logged in |
| `PermissionRequiredMixin` | `@permission_required("app.perm")` | A permission |
| `UserPassesTestMixin` | `@user_passes_test(fn)` | Passing a test |

!!! danger "The mixin always FIRST in the inheritance"
    `class V(LoginRequiredMixin, DetailView)` — the mixin on the left intercepts
    first. Inverted, the gate doesn't run. (See [views CBV](views-cbv.md) about MRO.)

### Permissions: the four automatic ones + yours

Every model gets 4 automatic permissions: `add`, `change`, `delete`, `view`. The
full name is `app_label.action_model`:

```python
request.user.has_perm("blog.add_post")
request.user.has_perm("blog.delete_comment")
```

Extra permissions, in the model's `Meta`:

```python
class Report(models.Model):
    class Meta:
        permissions = [
            ("can_export", "Can export reports"),
        ]
# usage: request.user.has_perm("blog.can_export")
```

### Groups: badges in batches

Think like a child: a **group** is a little box of badges. Instead of giving 10
permissions to each person, you create the "Editors" group with those permissions
and just put people in the box.

```python
from django.contrib.auth.models import Group, Permission

editores = Group.objects.create(name="Editors")
editores.permissions.add(Permission.objects.get(codename="add_post"))
user.groups.add(editores)        # inherits all the group's permissions
```

### Password hashing

```python
from django.contrib.auth import get_user_model, authenticate

User = get_user_model()
user = User.objects.create_user("ana", password="segredo123")  # already hashes

user.check_password("segredo123")   # True
user.check_password("errado")        # False

# authenticate (checks credentials)
u = authenticate(username="ana", password="segredo123")   # user or None
```

!!! danger "Never store or compare a raw password"
    `create_user`/`set_password` hash; `check_password` compares safely. Never do
    `User(password="...")` directly — that saves plain text.

### Custom user (do it early!)

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

!!! warning "Swap the `User` at the start of the project"
    Changing `AUTH_USER_MODEL` after the database exists is painful (complicated
    migrations). If there's **any** chance you'll need extra fields on the user,
    create the custom model right in the first migration. And always reference it
    via `settings.AUTH_USER_MODEL` (models) or `get_user_model()` (code).

## Recap

- Authentication = "who are you"; permissions = "what you can do".
- `request.user` always exists (`AnonymousUser` for a visitor);
  `is_authenticated`/`is_staff`/`is_superuser`.
- Login/logout/password are ready-made views; configure the `*_URL`s in the settings.
- Protect: mixin (CBV, always 1st) or decorator (function) —
  `LoginRequired`/`PermissionRequired`/`UserPassesTest`.
- 4 automatic permissions per model + extras in `Meta`; **groups** give
  permissions in batches.
- Passwords always hashed (`create_user`/`check_password`). Swap the `User` for a
  custom one **at the start** and use `get_user_model()`.

You now have the reference for Django's main layers. 🎉 Go back to the
[Tutorial](../tutorial/project-setup.md) to see them together, or explore any
reference page as you like.
