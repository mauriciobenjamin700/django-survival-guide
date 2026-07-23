# Reference: organizing HTML, CSS and JS

!!! quote "Think like a child 🧒"
    Imagine your bedroom: clothes in a wardrobe, toys in a box, books on the
    shelf. If everything is dumped on the floor, you can never find anything.
    This is the guide to **where each thing lives** in a Django project: the HTML
    (templates), the CSS and the JS (static files) — each in its own drawer, with
    a predictable name.

## Use case

You have the `blog` app and you want to add a `style.css`, a `blog.js` and the
HTML pages. Where does each file go? Django's rule: **each app carries its own
files**, inside a subfolder named after the app (the *namespace*).

```text
apps/blog/
├── static/
│   └── blog/                 # namespace = app name
│       ├── css/style.css
│       └── js/blog.js
└── templates/
    └── blog/                 # same namespace
        ├── post_list.html
        └── post_detail.html
```

```django
{% load static %}
<link rel="stylesheet" href="{% static 'blog/css/style.css' %}">
<script src="{% static 'blog/js/blog.js' %}" defer></script>
```

## Possibilities

### Why the subfolder named after the app (namespace)

Think like a child: if two apps each had a **loose** `style.css`, Django wouldn't
know which one to serve. By putting them inside `blog/` and `shop/`, you ask for
`blog/css/style.css` — no ambiguity. This applies to static files **and**
templates.

!!! danger "Never put `style.css` directly in `static/`"
    `app/static/style.css` collides with any other app's file. Always
    `app/static/<app>/...`. Same for templates: `app/templates/<app>/...`.

### App-level × project-level

| Where | For what | Setting |
| --- | --- | --- |
| `app/static/<app>/` | Files for **that** app | `APP_DIRS`/`app_directories` (automatic) |
| `assets/` at the root | **Global** files (theme, favicon, base CSS) | `STATICFILES_DIRS` |

```python
# config/settings.py
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "assets"]      # project-wide global static files
STATIC_ROOT = BASE_DIR / "staticfiles"         # collectstatic destination (production)
```

!!! warning "`STATICFILES_DIRS` ≠ `STATIC_ROOT`"
    - **`STATICFILES_DIRS`** = extra **source** folders that you write.
    - **`STATIC_ROOT`** = the **destination** folder where `collectstatic`
      **gathers** everything for production. Never point one at the other.

### Template structure: base + inheritance + partials

Think like a child: `base.html` is the frame of the house; each page slots in its
own picture; the **partials** are pieces you reuse (the header, a card).

```text
templates/                      # project globals (via DIRS)
├── base.html                   # skeleton: <head>, nav, blocks
└── partials/
    ├── _navbar.html
    └── _footer.html

apps/blog/templates/blog/       # app-level (via APP_DIRS)
├── post_list.html              # {% extends "base.html" %}
└── post_detail.html
```

```django title="templates/base.html" hl_lines="6 12 14"
{% load static %}
<!doctype html>
<html lang="en">
<head>
  <title>{% block title %}Blog{% endblock %}</title>
  <link rel="stylesheet" href="{% static 'css/base.css' %}">
  {% block extra_css %}{% endblock %}      {# (1)! #}
</head>
<body>
  {% include "partials/_navbar.html" %}
  {% block content %}{% endblock %}
  <script src="{% static 'js/base.js' %}" defer></script>
  {% block extra_js %}{% endblock %}       {# (2)! #}
</body>
</html>
```

1. Each page injects its page-specific CSS here, without duplicating the `<head>`.
2. Same for page-specific JS.

```django title="blog/post_list.html"
{% extends "base.html" %}
{% load static %}

{% block title %}Posts — Blog{% endblock %}

{% block extra_css %}
  <link rel="stylesheet" href="{% static 'blog/css/style.css' %}">
{% endblock %}

{% block content %}
  ...
{% endblock %}

{% block extra_js %}
  <script src="{% static 'blog/js/blog.js' %}" defer></script>
{% endblock %}
```

!!! tip "Convention: partials start with `_`"
    Naming partials like `_navbar.html` makes it clear that they're pieces
    included by other templates, not full pages. `{% include %}` to insert,
    `{% extends %}`/`{% block %}` to inherit.

### A complete recommended structure

```text
project/
├── assets/                     # global static files (STATICFILES_DIRS)
│   ├── css/base.css
│   ├── js/base.js
│   └── img/logo.svg
├── templates/                  # global templates (DIRS)
│   ├── base.html
│   └── partials/
└── apps/
    └── blog/
        ├── static/blog/        # app static files
        │   ├── css/
        │   └── js/
        └── templates/blog/     # app templates
```

### `{% static %}` — never write the path by hand

```django
{% load static %}
<img src="{% static 'img/logo.svg' %}" alt="logo">
```

!!! danger "Don't hardcode `/static/...` in the HTML"
    In production `STATIC_URL` may change (CDN, prefix, hashed name with
    WhiteNoise's manifest). `{% static %}` resolves the right path in every
    environment; a hardcoded `/static/img/logo.svg` breaks the moment the name
    gains a hash.

### And when the front-end grows? (bundlers)

For simple CSS/JS, serving static files directly is enough — that's what we do.
When you adopt Sass, TypeScript or a framework (React/Vue):

1. A **bundler** (Vite, esbuild) compiles and produces optimized files.
2. Configure the bundler's **output** to a folder inside `STATICFILES_DIRS`
   (e.g. `assets/dist/`).
3. `collectstatic` picks up the result like any other static file.
4. Libraries such as `django-vite` help match the hashed files in the template.

!!! tip "Start simple"
    Don't plug in a bundler before you need it. `{% static %}` + per-app CSS/JS
    folders solves the majority of projects. The bundler comes in when there's a
    real front-end build.

### Production (quick recap)

In production you run `collectstatic` (gathers everything into `STATIC_ROOT`) and
serve it with **WhiteNoise** or a CDN. The storage and deploy details are in
**[Static and media files](static-media.md)** and **[Storages](storages.md)**.

!!! quote "📖 In the official docs"
    - [How to manage static files](https://docs.djangoproject.com/en/stable/howto/static-files/)
    - [Templates](https://docs.djangoproject.com/en/stable/topics/templates/)

## Recap

- Each app carries its files under a **namespace**:
  `app/static/<app>/...` and `app/templates/<app>/...`. Never drop `style.css`
  directly in `static/`.
- Project globals: `assets/` (via `STATICFILES_DIRS`) and `templates/` (via
  `DIRS`). `STATIC_ROOT` is only the `collectstatic` destination.
- Templates: `base.html` + `{% block %}` + partials `_name.html`; page-specific
  CSS/JS go into `{% block extra_css %}`/`{% block extra_js %}`.
- Always `{% static %}` — never a hardcoded path.
- Large front-end → bundler (Vite/esbuild) with output in `STATICFILES_DIRS`; but
  start simple.

For the mechanics of STATIC×MEDIA and production, see
**[Static and media files](static-media.md)**.
