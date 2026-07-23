# Templates

A **template** is an HTML file with special markup that Django fills
with data. It's the *presentation* layer: the view delivers a context dictionary,
the template decides how to display it.

## Where templates live

Django looks for templates in two places:

- **`templates/`** at the project root — for global files (the `base.html`).
- **`apps/<app>/templates/<app>/`** — for each app's (the namespace avoids
  collision).

We configure this in `settings.py`:

```python
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # (1)!
        "APP_DIRS": True,                   # (2)!
        # ...
    },
]
```

1. The project's global templates folder.
2. Makes Django also look in `<app>/templates/` of each installed app.

!!! tip "Why `blog/post_list.html` and not just `post_list.html`?"
    The real file is `apps/blog/templates/blog/post_list.html`. That extra
    `blog/` folder creates a *namespace*: if two apps had `post_list.html`, the
    Django wouldn't know which to use. With the prefix, you ask for `blog/post_list.html`.

## The template language

Three basic constructs:

| Syntax | What for | Example |
| --- | --- | --- |
| `{{ ... }}` | Display a value | `{{ post.title }}` |
| `{% ... %}` | Logic (tags) | `{% for p in posts %}` |
| `\| filter` | Transform a value | `{{ post.body\|truncatewords:30 }}` |

!!! note "No heavy logic in the template"
    The language is **deliberately limited** — you can iterate and use conditionals,
    but not write business rules. That's intentional: logic stays in
    Python (models/views), the template only presents.

## Template inheritance: the `base.html`

Instead of repeating `<html>`, header, and navigation on every page, we define a
**skeleton** with **blocks** that pages fill in:

```django title="templates/base.html"
<!doctype html>
<html lang="pt-br">
<head>
  <title>{% block title %}Blog{% endblock %}</title>
</head>
<body>
  <header>
    <a href="{% url 'blog:post-list' %}">📓 Blog</a>
    {% if user.is_authenticated %}
      <a href="{% url 'blog:post-create' %}">New post</a>
      <a href="{% url 'logout' %}">Logout ({{ user.username }})</a>
    {% else %}
      <a href="{% url 'login' %}">Login</a>
    {% endif %}
  </header>

  {% block content %}{% endblock %}
</body>
</html>
```

And each page **extends** the base and fills in the blocks:

```django title="blog/post_list.html" hl_lines="1 3"
{% extends "base.html" %}

{% block content %}
  <h1>Latest posts</h1>
  {% for post in posts %}
    <article>
      <h2><a href="{{ post.get_absolute_url }}">{{ post.title }}</a></h2>
      <p>by {{ post.author }} · {{ post.published_at|date:"d M Y" }}</p>
      <p>{{ post.body|truncatewords:30 }}</p>
    </article>
  {% empty %}
    <p>No posts yet.</p>
  {% endfor %}
{% endblock %}
```

- **`{% extends %}`** — inherits from `base.html`. Must be the **first** line.
- **`{% block content %}`** — fills the hole defined in the base.
- **`{% for %} ... {% empty %}`** — the `{% empty %}` runs when the list is empty.
  Much cleaner than checking the size beforehand.
- **`|date:"d M Y"`** — a date formatting filter.
- **`{{ post.get_absolute_url }}`** — we call the model's method directly in the
  template (without parentheses).

!!! info "Templates call methods without parentheses"
    `{{ post.get_absolute_url }}` executes the method. The template language
    resolves attribute → dictionary item → method, automatically. You do **not**
    write `()`.

## Pagination in the template

Since the `ListView` has `paginate_by = 5`, it exposes `page_obj` and `is_paginated`:

```django
{% if is_paginated %}
  {% if page_obj.has_previous %}
    <a href="?page={{ page_obj.previous_page_number }}">← Newer</a>
  {% endif %}
  <span>Page {{ page_obj.number }} of {{ page_obj.paginator.num_pages }}</span>
  {% if page_obj.has_next %}
    <a href="?page={{ page_obj.next_page_number }}">Older →</a>
  {% endif %}
{% endif %}
```

## Security: automatic escaping

Django **escapes HTML automatically**. If a comment contains
`<script>`, it's displayed as text, not executed — protection against XSS for
free.

!!! danger "Careful with `|safe`"
    The `|safe` filter turns off escaping. Only use it on content **you trust**
    (never on text coming from the user). When in doubt, don't use it.

!!! quote "📖 In the official docs"
    - [Templates](https://docs.djangoproject.com/en/stable/topics/templates/)

## Recap

- Templates are HTML + `{{ values }}`, `{% tags %}`, and `|filters`.
- Inheritance with `{% extends %}` + `{% block %}` eliminates repetition.
- `{% for %}...{% empty %}` handles an empty list elegantly.
- URLs always via `{% url 'blog:...' %}`; model methods without parentheses.
- Escaping is automatic — only break it with `|safe` on trusted content.

We know how to display data. What's left is to **receive** data from the user with validation — the
**[Forms](forms.md)**.
