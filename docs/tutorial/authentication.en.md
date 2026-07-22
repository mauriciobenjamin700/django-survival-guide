# Authentication

Django already ships with a complete **authentication system**: a user model,
login/logout, sessions, hashed passwords, and permission control. You rarely
need to write this from scratch.

!!! quote "What you get out of the box"
    - A `User` model (`django.contrib.auth`).
    - Login/logout views.
    - Secure password hashing (never in plain text).
    - `request.user` available in every view.
    - Mixins and decorators to protect pages.

## The logged-in user: `request.user`

Thanks to the `AuthenticationMiddleware`, every request carries the current user:

```python
if request.user.is_authenticated:
    print(request.user.username)
else:
    print("visitante anônimo")
```

In the template, the same object is available as `user`:

```django
{% if user.is_authenticated %}
  <a href="{% url 'blog:post-create' %}">New post</a>
  <a href="{% url 'logout' %}">Logout ({{ user.username }})</a>
{% else %}
  <a href="{% url 'login' %}">Login</a>
{% endif %}
```

## Login and logout: ready-made views

We don't write these views — we use Django's own, just pointing the routes:

```python
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
```

The `LoginView` looks for a template at `registration/login.html`. Ours:

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

And we configure where to go in each case, in `settings.py`:

```python
LOGIN_URL: str = "login"                       # (1)!
LOGIN_REDIRECT_URL: str = "blog:post-list"     # (2)!
LOGOUT_REDIRECT_URL: str = "blog:post-list"    # (3)!
```

1. Where to send anyone who tries to access a protected page without logging in.
2. Where to go after logging in successfully.
3. Where to go after logging out.

## Protecting views: `LoginRequiredMixin`

Since we use class-based views, we protect them with a **mixin** — composition,
without touching the view's logic:

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView


class PostCreateView(LoginRequiredMixin, CreateView):
    """Only logged-in users can create posts."""
    # ...
```

Anyone not logged in is redirected to `LOGIN_URL`, with the original destination
preserved in the `?next=` parameter, so they return after logging in.

!!! warning "The mixin comes first"
    Always `class MyView(LoginRequiredMixin, GenericView)`. If you reverse it, the
    mixin doesn't intercept the request in time. Left-to-right order
    defines the inheritance chain (MRO).

!!! info "Function views? Use the decorator"
    The equivalent for function views is `@login_required`:
    ```python
    from django.contrib.auth.decorators import login_required

    @login_required
    def minha_view(request): ...
    ```
    Mixin for classes, decorator for functions — same idea.

## Passwords: never in plain text

Django **hashes** passwords automatically. You never store nor compare
the raw password:

```python
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.create_user(username="ana", password="segredo123")
# a senha é hasheada antes de ir ao banco

user.check_password("segredo123")  # -> True
user.check_password("errado")       # -> False
```

The validators in `AUTH_PASSWORD_VALIDATORS` (minimum length, common passwords,
etc.) enforce strong passwords at signup.

!!! tip "`get_user_model()` instead of importing `User`"
    Always reference the user via `settings.AUTH_USER_MODEL` (in models) or
    `get_user_model()` (in code). This way, if the project switches to a custom
    user, nothing breaks. That's what we did in the `Author` model.

## Permissions and groups (overview)

Beyond "logged in or not", Django has **permissions** per model
(`add`, `change`, `delete`, `view`) and **groups** that bundle permissions. For
per-permission gating in CBVs, there's the `PermissionRequiredMixin`:

```python
from django.contrib.auth.mixins import PermissionRequiredMixin


class PostDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = "blog.delete_post"
```

## Recap

- Authentication comes ready: `User`, login/logout, sessions, password hashing.
- `request.user` / `user` in the template tell who is logged in.
- Point routes to `LoginView`/`LogoutView` and configure the `*_URL` settings.
- Protect CBVs with `LoginRequiredMixin` (always first in the inheritance).
- Passwords are hashed; use `create_user`/`check_password` and `get_user_model()`.

You've completed the **Tutorial**! You have a complete, typed, object-oriented blog.
Now let's expose those same data as a **[REST API with DRF](../advanced/drf.md)**.
