# Templates

Um **template** é um arquivo HTML com marcações especiais que o Django preenche
com dados. É a camada de *apresentação*: a view entrega um dicionário de contexto,
o template decide como exibir.

## Onde os templates ficam

O Django procura templates em dois lugares:

- **`templates/`** na raiz do projeto — para arquivos globais (o `base.html`).
- **`apps/<app>/templates/<app>/`** — para os de cada app (o namespace evita
  colisão).

Configuramos isso em `settings.py`:

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

1. Pasta global de templates do projeto.
2. Faz o Django também procurar em `<app>/templates/` de cada app instalado.

!!! tip "Por que `blog/post_list.html` e não só `post_list.html`?"
    O arquivo real é `apps/blog/templates/blog/post_list.html`. Essa pasta
    `blog/` extra cria um *namespace*: se dois apps tivessem `post_list.html`, o
    Django não saberia qual usar. Com o prefixo, você pede `blog/post_list.html`.

## A linguagem de templates

Três construções básicas:

| Sintaxe | Para quê | Exemplo |
| --- | --- | --- |
| `{{ ... }}` | Exibir um valor | `{{ post.title }}` |
| `{% ... %}` | Lógica (tags) | `{% for p in posts %}` |
| `\| filtro` | Transformar valor | `{{ post.body\|truncatewords:30 }}` |

!!! note "Sem lógica pesada no template"
    A linguagem é **propositalmente limitada** — dá para iterar e condicionar,
    mas não para escrever regras de negócio. Isso é intencional: lógica fica em
    Python (models/views), o template só apresenta.

## Herança de templates: o `base.html`

Em vez de repetir `<html>`, cabeçalho e navegação em toda página, definimos um
**esqueleto** com **blocos** que as páginas preenchem:

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

E cada página **estende** o base e preenche os blocos:

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

- **`{% extends %}`** — herda de `base.html`. Deve ser a **primeira** linha.
- **`{% block content %}`** — preenche o buraco definido no base.
- **`{% for %} ... {% empty %}`** — o `{% empty %}` roda quando a lista é vazia.
  Muito mais limpo que checar o tamanho antes.
- **`|date:"d M Y"`** — filtro de formatação de data.
- **`{{ post.get_absolute_url }}`** — chamamos o método do modelo direto no
  template (sem parênteses).

!!! info "Templates chamam métodos sem parênteses"
    `{{ post.get_absolute_url }}` executa o método. A linguagem de templates
    resolve atributo → item de dicionário → método, automaticamente. Você **não**
    escreve `()`.

## Paginação no template

Como a `ListView` tem `paginate_by = 5`, ela expõe `page_obj` e `is_paginated`:

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

## Segurança: escaping automático

O Django **escapa HTML automaticamente**. Se um comentário contém
`<script>`, ele é exibido como texto, não executado — proteção contra XSS de
graça.

!!! danger "Cuidado com `|safe`"
    O filtro `|safe` desliga o escaping. Só use em conteúdo **que você confia**
    (nunca em texto vindo do usuário). Na dúvida, não use.

## Recapitulando

- Templates são HTML + `{{ valores }}`, `{% tags %}` e `|filtros`.
- Herança com `{% extends %}` + `{% block %}` elimina repetição.
- `{% for %}...{% empty %}` trata lista vazia elegantemente.
- URLs sempre via `{% url 'blog:...' %}`; métodos do modelo sem parênteses.
- Escaping é automático — só quebre com `|safe` em conteúdo confiável.

Sabemos exibir dados. Falta **receber** dados do usuário com validação — os
**[Formulários](forms.md)**.
