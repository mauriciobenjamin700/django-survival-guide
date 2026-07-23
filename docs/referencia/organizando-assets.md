# Referência: organizando HTML, CSS e JS

!!! quote "Pensa como criança 🧒"
    Imagine seu quarto: as roupas num armário, os brinquedos numa caixa, os
    livros na estante. Se tudo ficar jogado no chão, você nunca acha nada. Este é
    o guia de **onde cada coisa mora** num projeto Django: o HTML (templates), o
    CSS e o JS (estáticos) — cada um na sua gaveta, com um nome previsível.

## Caso de uso

Você tem o app `blog` e quer pôr um `style.css`, um `blog.js` e as páginas HTML.
Onde cada arquivo vai? A regra do Django: **cada app carrega seus próprios
arquivos**, dentro de uma subpasta com o nome do app (o *namespace*).

```text
apps/blog/
├── static/
│   └── blog/                 # namespace = nome do app
│       ├── css/style.css
│       └── js/blog.js
└── templates/
    └── blog/                 # mesmo namespace
        ├── post_list.html
        └── post_detail.html
```

```django
{% load static %}
<link rel="stylesheet" href="{% static 'blog/css/style.css' %}">
<script src="{% static 'blog/js/blog.js' %}" defer></script>
```

## Possibilidades

### Por que a subpasta com o nome do app (namespace)

Pensa como criança: se dois apps tivessem, cada um, um `style.css` **solto**, o
Django não saberia qual entregar. Pondo dentro de `blog/` e `loja/`, você pede
`blog/css/style.css` — sem ambiguidade. Vale para estáticos **e** templates.

!!! danger "Nunca ponha `style.css` direto em `static/`"
    `app/static/style.css` colide com o de qualquer outro app. Sempre
    `app/static/<app>/...`. O mesmo para templates: `app/templates/<app>/...`.

### Do app × do projeto

| Onde | Para quê | Setting |
| --- | --- | --- |
| `app/static/<app>/` | Arquivos **daquele** app | `APP_DIRS`/`app_directories` (automático) |
| `assets/` na raiz | Arquivos **globais** (tema, favicon, CSS base) | `STATICFILES_DIRS` |

```python
# config/settings.py
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "assets"]      # estáticos globais do projeto
STATIC_ROOT = BASE_DIR / "staticfiles"         # destino do collectstatic (produção)
```

!!! warning "`STATICFILES_DIRS` ≠ `STATIC_ROOT`"
    - **`STATICFILES_DIRS`** = pastas de **origem** extras que você escreve.
    - **`STATIC_ROOT`** = pasta de **destino** onde o `collectstatic` **junta**
      tudo para produção. Nunca aponte uma para a outra.

### Estrutura de templates: base + herança + parciais

Pensa como criança: o `base.html` é a moldura da casa; cada página encaixa seu
quadro; as **parciais** são peças que você reaproveita (o cabeçalho, um card).

```text
templates/                      # globais do projeto (via DIRS)
├── base.html                   # esqueleto: <head>, nav, blocos
└── partials/
    ├── _navbar.html
    └── _footer.html

apps/blog/templates/blog/       # do app (via APP_DIRS)
├── post_list.html              # {% extends "base.html" %}
└── post_detail.html
```

```django title="templates/base.html" hl_lines="6 12 14"
{% load static %}
<!doctype html>
<html lang="pt-br">
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

1. Cada página injeta seu CSS específico aqui, sem duplicar o `<head>`.
2. Idem para JS específico da página.

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

!!! tip "Convenção: parciais começam com `_`"
    Nomear parciais como `_navbar.html` deixa claro que são pedaços incluídos por
    outros templates, não páginas completas. `{% include %}` para inserir,
    `{% extends %}`/`{% block %}` para herdar.

### Uma estrutura completa recomendada

```text
projeto/
├── assets/                     # estáticos globais (STATICFILES_DIRS)
│   ├── css/base.css
│   ├── js/base.js
│   └── img/logo.svg
├── templates/                  # templates globais (DIRS)
│   ├── base.html
│   └── partials/
└── apps/
    └── blog/
        ├── static/blog/        # estáticos do app
        │   ├── css/
        │   └── js/
        └── templates/blog/     # templates do app
```

### `{% static %}` — nunca escreva o caminho na mão

```django
{% load static %}
<img src="{% static 'img/logo.svg' %}" alt="logo">
```

!!! danger "Não escreva `/static/...` fixo no HTML"
    Em produção o `STATIC_URL` pode mudar (CDN, prefixo, hash no nome com o
    manifest do WhiteNoise). O `{% static %}` resolve o caminho certo em cada
    ambiente; um `/static/img/logo.svg` fixo quebra quando o nome ganha hash.

### E quando o front-end cresce? (bundlers)

Para CSS/JS simples, servir estáticos direto basta — é o que fazemos. Quando você
adota Sass, TypeScript ou um framework (React/Vue):

1. Um **bundler** (Vite, esbuild) compila e gera arquivos otimizados.
2. Configure a **saída** do bundler para uma pasta em `STATICFILES_DIRS` (ex.:
   `assets/dist/`).
3. O `collectstatic` recolhe o resultado como qualquer outro estático.
4. Bibliotecas como `django-vite` ajudam a casar os arquivos com hash no template.

!!! tip "Comece simples"
    Não plugue um bundler antes de precisar. `{% static %}` + CSS/JS em pastas
    por app resolve a maioria dos projetos. O bundler entra quando há build de
    front-end de verdade.

### Produção (recap rápido)

Em produção você roda `collectstatic` (junta tudo em `STATIC_ROOT`) e serve com
**WhiteNoise** ou uma CDN. Os detalhes de armazenamento e deploy estão em
**[Arquivos estáticos e media](static-media.md)** e **[Storages](storages.md)**.

!!! quote "📖 Na documentação oficial"
    - [How to manage static files](https://docs.djangoproject.com/en/stable/howto/static-files/)
    - [Templates](https://docs.djangoproject.com/en/stable/topics/templates/)

## Recap

- Cada app carrega seus arquivos sob um **namespace**:
  `app/static/<app>/...` e `app/templates/<app>/...`. Nunca solte `style.css`
  direto em `static/`.
- Globais do projeto: `assets/` (via `STATICFILES_DIRS`) e `templates/` (via
  `DIRS`). `STATIC_ROOT` é só destino do `collectstatic`.
- Templates: `base.html` + `{% block %}` + parciais `_nome.html`; CSS/JS
  específicos entram em `{% block extra_css %}`/`{% block extra_js %}`.
- Sempre `{% static %}` — nunca caminho fixo.
- Front-end grande → bundler (Vite/esbuild) com saída em `STATICFILES_DIRS`; mas
  comece simples.

Para a mecânica de STATIC×MEDIA e produção, veja
**[Arquivos estáticos e media](static-media.md)**.
