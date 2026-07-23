# Reference: templates (tags and filters)

!!! quote "Think like a child 🧒"
    A **template** is a coloring drawing with blank spaces. Django receives the
    drawing (the HTML) and fills the blanks with the data the view handed over. The
    **tags** (`{% %}`) are the scissors and the glue — they cut, repeat, choose.
    The **filters** (`|`) are the crayons — they change how a value looks before it
    shows up.

## Use case

The view sends a list of `posts`. You want to display each title as a link, the
date formatted, and a message if the list is empty:

```django
{% extends "base.html" %}

{% block content %}
  <h1>Posts</h1>
  {% for post in posts %}
    <article>
      <h2><a href="{{ post.get_absolute_url }}">{{ post.title }}</a></h2>
      <p>{{ post.published_at|date:"d/m/Y" }}</p>
    </article>
  {% empty %}
    <p>No posts yet.</p>
  {% endfor %}
{% endblock %}
```

Three constructs: `{{ value }}` displays, `{% tag %}` decides, `|filter`
transforms. Let's go through the catalog.

## Possibilities

### The three syntaxes

| Syntax | For what | Example |
| --- | --- | --- |
| `{{ ... }}` | Display a value | `{{ post.title }}` |
| `{% ... %}` | Logic (tags) | `{% if user.is_staff %}` |
| `{{ x\|filter }}` | Transform a value | `{{ name\|upper }}` |

!!! info "The dot does everything: attribute, item, method"
    `{{ post.title }}` tries, in this order: attribute `post.title`, item
    `post["title"]`, method `post.title()`. That's why `{{ post.get_absolute_url }}`
    calls the method **without** parentheses. Think like a child: the dot is a
    little key that opens any of the doors.

### Essential tags

| Tag | What it does |
| --- | --- |
| `{% if %}` / `{% elif %}` / `{% else %}` / `{% endif %}` | Conditional |
| `{% for x in list %}` ... `{% empty %}` ... `{% endfor %}` | Loop (with empty case) |
| `{% block name %}` ... `{% endblock %}` | A hole children fill in |
| `{% extends "base.html" %}` | Inherit from a template |
| `{% include "partial.html" %}` | Insert another template |
| `{% url 'blog:post-list' %}` | Generate a URL by name |
| `{% csrf_token %}` | Security token in POST forms |
| `{% with total=items.count %}` | Create a local variable |
| `{% load %}` | Load extra tags/filters |

!!! tip "`{% extends %}` always on the first line"
    Template inheritance requires `{% extends %}` to be the **first** thing in the
    file. And `{% for %}` with `{% empty %}` is cleaner than checking the list's
    length beforehand.

### Loop variables: `forloop`

Inside a `{% for %}`, Django gives you a helper:

| Variable | Holds |
| --- | --- |
| `forloop.counter` | Count starting at 1 |
| `forloop.counter0` | Count starting at 0 |
| `forloop.first` | `True` on the first pass |
| `forloop.last` | `True` on the last pass |
| `forloop.revcounter` | Countdown |

```django
{% for post in posts %}
  <li class="{% if forloop.first %}destaque{% endif %}">{{ post.title }}</li>
{% endfor %}
```

### The most-used filters

| Filter | Effect | Example |
| --- | --- | --- |
| `date:"d/m/Y"` | Format a date | `{{ p.published_at\|date:"d/m/Y" }}` |
| `time:"H:i"` | Format a time | `{{ e.hora\|time:"H:i" }}` |
| `truncatewords:30` | Cut at N words | `{{ p.body\|truncatewords:30 }}` |
| `truncatechars:100` | Cut at N characters | — |
| `default:"—"` | Value if empty/falsy | `{{ p.subtitle\|default:"—" }}` |
| `length` | Size | `{{ posts\|length }}` |
| `linebreaks` | Line breaks → `<p>`/`<br>` | `{{ p.body\|linebreaks }}` |
| `upper` / `lower` / `title` | Text case | `{{ name\|title }}` |
| `pluralize` | "s" in the plural | `{{ n }} item{{ n\|pluralize }}` |
| `yesno:"yes,no"` | Boolean → text | `{{ active\|yesno:"yes,no" }}` |
| `floatformat:2` | Decimal places | `{{ price\|floatformat:2 }}` |
| `join:", "` | Join a list | `{{ tags\|join:", " }}` |
| `safe` | Do **not** escape HTML | `{{ content\|safe }}` |
| `escape` | Force escaping | — |

!!! danger "Escaping is automatic — watch out for `|safe`"
    Django escapes HTML on its own: a `<script>` in a comment becomes text, not
    code (protection against XSS). The `|safe` filter **turns off** that
    protection. Only use it on content **you** generated and trust — never on user
    text.

### Template inheritance

Think like a child: `base.html` is the frame; each page fits its picture into the
holes (`block`).

```django title="base.html"
<!doctype html>
<html>
<head><title>{% block title %}Blog{% endblock %}</title></head>
<body>
  <header>...</header>
  {% block content %}{% endblock %}
</body>
</html>
```

```django title="post_list.html" hl_lines="1"
{% extends "base.html" %}
{% block title %}Posts — Blog{% endblock %}
{% block content %}
  ...
{% endblock %}
```

!!! tip "`{{ block.super }}` reuses the parent's block"
    Inside a child's `{% block %}`, `{{ block.super }}` inserts the content the
    parent had, and you add around it — instead of replacing everything.

### Context processors: variables in every template

Configured in `TEMPLATES["OPTIONS"]["context_processors"]`, they inject variables
into **all** templates automatically. The defaults give you `user`, `request`,
`messages`. That's why you use `{{ user }}` without the view passing `user`.

### Custom tags and filters

When the built-in ones aren't enough, create your own in an
`apps/<app>/templatetags/blog_extras.py`:

```python
# apps/blog/templatetags/blog_extras.py
from django import template

register = template.Library()


@register.filter
def reading_time(text: str) -> int:
    """Estimate reading time in minutes (200 words/min)."""
    words = len(text.split())
    return max(1, words // 200)
```

```django
{% load blog_extras %}
<p>Reading: {{ post.body|reading_time }} min</p>
```

| Decorator | Creates |
| --- | --- |
| `@register.filter` | A filter (`{{ x\|my_filter }}`) |
| `@register.simple_tag` | A tag that returns a value |
| `@register.inclusion_tag("t.html")` | A tag that renders a sub-template |

!!! warning "Needs `__init__.py` and `{% load %}`"
    The `templatetags/` folder needs an `__init__.py`, and the app needs to be in
    `INSTALLED_APPS`. In the template, `{% load blog_extras %}` before using it.

!!! quote "📖 In the official docs"
    - [Templates](https://docs.djangoproject.com/en/stable/topics/templates/)
    - [Built-in template tags and filters](https://docs.djangoproject.com/en/stable/ref/templates/builtins/)

## Recap

- Three syntaxes: `{{ display }}`, `{% decide %}`, `|transform`.
- The dot accesses attribute/item/method (a method without parentheses).
- Key tags: `if`, `for`+`empty`, `block`/`extends`/`include`, `url`,
  `csrf_token`. Inside the loop, `forloop.*`.
- Filters: `date`, `truncatewords`, `default`, `linebreaks`, `pluralize`,
  `floatformat`... Escaping is automatic; `|safe` only on trusted content.
- Inheritance with `extends`/`block` (+`block.super`); context processors give you
  global variables; create custom tags/filters in `templatetags/`.

Templates display data that came from the ORM. Master the queries in the
**[full QuerySet API](querysets-api.md)**.
