# django-allauth

Django ships with username/password login. But sign-up with **email
verification**, **social login** (Google, GitHub) and account recovery takes work
to get right. `django-allauth` delivers all of it ready-made.

!!! quote "Think like a child 🧒"
    The building's gate already opens with your key (Django's login). allauth is the
    **complete doorman**: besides the key, it accepts your work badge (social
    login), confirms you're really you by email, and handles "I forgot my password".

## Installation and configuration

```bash
uv add "django-allauth[socialaccount]"
```

```python
# settings.py
INSTALLED_APPS = [
    "django.contrib.sites",              # (1)!
    "allauth",
    "allauth.account",
    "allauth.socialaccount",             # social login (optional)
    "allauth.socialaccount.providers.google",   # one provider
    # ...
]

MIDDLEWARE = [
    # ...
    "allauth.account.middleware.AccountMiddleware",   # (2)!
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",       # normal admin login
    "allauth.account.auth_backends.AuthenticationBackend",  # allauth login
]

SITE_ID = 1
```

1. allauth depends on the `sites` framework. `SITE_ID = 1` points to the default
    site.
2. `AccountMiddleware` is **mandatory** in current versions — forgetting it causes
    an error on the very first access.

```python
# urls.py
urlpatterns = [
    path("accounts/", include("allauth.urls")),   # login, signup, reset, social
]
```

```bash
python manage.py migrate
```

Done: `/accounts/login/`, `/accounts/signup/`, `/accounts/password/reset/` already
work.

## What you can do

### Configure account behavior

Several options were renamed/restructured in recent versions (they remain
separate `ACCOUNT_*` settings, not a single dictionary):

```python
# settings.py
ACCOUNT_LOGIN_METHODS = {"email"}            # log in by email (not username)
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "mandatory"     # require email verification
ACCOUNT_EMAIL_REQUIRED = True
```

| Option | What it controls |
| --- | --- |
| `ACCOUNT_LOGIN_METHODS` | Log in by `email`, `username` or both |
| `ACCOUNT_EMAIL_VERIFICATION` | `"mandatory"`, `"optional"` or `"none"` |
| `ACCOUNT_SIGNUP_FIELDS` | Sign-up fields (`*` = required) |
| `ACCOUNT_RATE_LIMITS` | Attempt limits (anti brute-force) |

!!! warning "allauth's settings keys change between versions"
    Major versions renamed settings (e.g. `ACCOUNT_AUTHENTICATION_METHOD` →
    `ACCOUNT_LOGIN_METHODS`). Always check the docs **for the version you installed**
    — copying an old tutorial leads to silent configuration errors.

### Social login (e.g. Google)

Think like a child: the "Sign in with Google" button is a trust agreement —
Google confirms who you are and allauth creates/links the account.

1. Register the app in the provider's console (Google Cloud) and grab the `client_id` +
   `secret`.
2. Configure it in `settings.py` **or** register it in the admin (the *Social
   application* model):

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

3. The login button shows up at `/accounts/login/`.

!!! danger "Provider secrets come from the environment"
    `client_id` and `secret` are credentials — read them from environment variables, never
    hardcode them in versioned code. See [settings](../referencia/settings.md).

### Customize the templates

allauth ships ready-made templates, but ugly ones. Override them by creating files with the
same path in `templates/account/` (e.g. `templates/account/login.html`) — Django
finds yours first. Extend your `base.html` to keep your identity.

## When to use it (and when not)

!!! tip "Use allauth when..."
    You need **social login**, robust **email verification**, or a complete
    account flow. Doing this by hand is easy to get wrong (security).

!!! warning "You may not need it if..."
    The project is a pure API for a mobile/SPA app — then the flow is by **token/JWT**
    (see [friends](afins.md) → `djangorestframework-simplejwt`), and allauth has
    `allauth.headless` for that case, but evaluate whether a simple JWT already does the job.

## Recap

- allauth delivers sign-up, email verification, recovery and **social login**.
- Ritual: `uv add` → apps (`sites` + `allauth.*`) → `AccountMiddleware` →
  `AUTHENTICATION_BACKENDS` → `SITE_ID` → `include("allauth.urls")` → `migrate`.
- Behavior via `ACCOUNT_*`/`SOCIALACCOUNT_*` settings (names change between
  versions — check yours).
- Provider secrets in the environment; customize by overriding `templates/account/`.

!!! quote "📖 In the official docs"
    - [django-allauth](https://docs.allauth.org/)

Login sorted. And heavy tasks that don't fit in the request?
**[Celery](celery.md)**.
