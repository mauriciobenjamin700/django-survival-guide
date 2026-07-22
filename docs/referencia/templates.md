# Referência: templates (tags e filtros)

!!! quote "Pensa como criança 🧒"
    Um **template** é um desenho de colorir com espaços em branco. O Django
    recebe o desenho (o HTML) e preenche os espaços com os dados que a view
    entregou. As **tags** (`{% %}`) são as tesouras e a cola — cortam, repetem,
    escolhem. Os **filtros** (`|`) são os lápis de cor — mudam a aparência de um
    valor antes de ele aparecer.

## Caso de uso

A view manda uma lista de `posts`. Você quer exibir cada título como link, a data
formatada, e uma mensagem se a lista estiver vazia:

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
    <p>Nenhum post ainda.</p>
  {% endfor %}
{% endblock %}
```

Três construções: `{{ valor }}` exibe, `{% tag %}` decide, `|filtro` transforma.
Vamos ver o catálogo.

## Possibilidades

### As três sintaxes

| Sintaxe | Para quê | Exemplo |
| --- | --- | --- |
| `{{ ... }}` | Exibir um valor | `{{ post.title }}` |
| `{% ... %}` | Lógica (tags) | `{% if user.is_staff %}` |
| `{{ x\|filtro }}` | Transformar um valor | `{{ nome\|upper }}` |

!!! info "Ponto faz tudo: atributo, item, método"
    `{{ post.title }}` tenta, nessa ordem: atributo `post.title`, item
    `post["title"]`, método `post.title()`. Por isso `{{ post.get_absolute_url }}`
    chama o método **sem** parênteses. Pensa como criança: o ponto é uma
    chavinha que abre qualquer uma das portas.

### Tags essenciais

| Tag | O que faz |
| --- | --- |
| `{% if %}` / `{% elif %}` / `{% else %}` / `{% endif %}` | Condicional |
| `{% for x in lista %}` ... `{% empty %}` ... `{% endfor %}` | Loop (com caso-vazio) |
| `{% block nome %}` ... `{% endblock %}` | Buraco que filhos preenchem |
| `{% extends "base.html" %}` | Herdar de um template |
| `{% include "parcial.html" %}` | Inserir outro template |
| `{% url 'blog:post-list' %}` | Gerar uma URL pelo nome |
| `{% csrf_token %}` | Token de segurança em forms POST |
| `{% with total=itens.count %}` | Criar variável local |
| `{% load %}` | Carregar tags/filtros extras |

!!! tip "`{% extends %}` sempre na primeira linha"
    Herança de template exige que `{% extends %}` seja a **primeira** coisa do
    arquivo. E `{% for %}` com `{% empty %}` é mais limpo que checar o tamanho da
    lista antes.

### Variáveis do loop: `forloop`

Dentro de um `{% for %}`, o Django te dá um ajudante:

| Variável | Vale |
| --- | --- |
| `forloop.counter` | Contagem começando em 1 |
| `forloop.counter0` | Contagem começando em 0 |
| `forloop.first` | `True` na primeira volta |
| `forloop.last` | `True` na última volta |
| `forloop.revcounter` | Contagem regressiva |

```django
{% for post in posts %}
  <li class="{% if forloop.first %}destaque{% endif %}">{{ post.title }}</li>
{% endfor %}
```

### Filtros mais usados

| Filtro | Efeito | Exemplo |
| --- | --- | --- |
| `date:"d/m/Y"` | Formata data | `{{ p.published_at\|date:"d/m/Y" }}` |
| `time:"H:i"` | Formata hora | `{{ e.hora\|time:"H:i" }}` |
| `truncatewords:30` | Corta em N palavras | `{{ p.body\|truncatewords:30 }}` |
| `truncatechars:100` | Corta em N caracteres | — |
| `default:"—"` | Valor se vazio/falsy | `{{ p.subtitle\|default:"—" }}` |
| `length` | Tamanho | `{{ posts\|length }}` |
| `linebreaks` | Quebras de linha → `<p>`/`<br>` | `{{ p.body\|linebreaks }}` |
| `upper` / `lower` / `title` | Caixa do texto | `{{ nome\|title }}` |
| `pluralize` | "s" no plural | `{{ n }} item{{ n\|pluralize }}` |
| `yesno:"sim,não"` | Booleano → texto | `{{ ativo\|yesno:"sim,não" }}` |
| `floatformat:2` | Casas decimais | `{{ preco\|floatformat:2 }}` |
| `join:", "` | Junta uma lista | `{{ tags\|join:", " }}` |
| `safe` | **Não** escapar HTML | `{{ conteudo\|safe }}` |
| `escape` | Forçar escape | — |

!!! danger "Escaping é automático — cuidado com `|safe`"
    O Django escapa HTML sozinho: um `<script>` num comentário vira texto, não
    código (proteção contra XSS). O filtro `|safe` **desliga** essa proteção. Só
    use em conteúdo que **você** gerou e confia — nunca em texto do usuário.

### Herança de template

Pensa como criança: o `base.html` é a moldura; cada página encaixa seu quadro nos
buracos (`block`).

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

!!! tip "`{{ block.super }}` reaproveita o bloco do pai"
    Dentro de um `{% block %}` do filho, `{{ block.super }}` insere o conteúdo
    que o pai tinha, e você acrescenta ao redor — em vez de substituir tudo.

### Context processors: variáveis em todo template

Configurados em `TEMPLATES["OPTIONS"]["context_processors"]`, injetam variáveis
em **todos** os templates automaticamente. Os padrões dão `user`, `request`,
`messages`. É por isso que você usa `{{ user }}` sem a view passar `user`.

### Custom tags e filtros

Quando os embutidos não bastam, crie os seus num
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
<p>Leitura: {{ post.body|reading_time }} min</p>
```

| Decorador | Cria |
| --- | --- |
| `@register.filter` | Um filtro (`{{ x\|meu_filtro }}`) |
| `@register.simple_tag` | Uma tag que retorna um valor |
| `@register.inclusion_tag("t.html")` | Uma tag que renderiza um sub-template |

!!! warning "Precisa de `__init__.py` e `{% load %}`"
    A pasta `templatetags/` precisa de um `__init__.py`, e o app precisa estar em
    `INSTALLED_APPS`. No template, `{% load blog_extras %}` antes de usar.

## Recap

- Três sintaxes: `{{ exibir }}`, `{% decidir %}`, `|transformar`.
- O ponto acessa atributo/item/método (método sem parênteses).
- Tags-chave: `if`, `for`+`empty`, `block`/`extends`/`include`, `url`,
  `csrf_token`. Dentro do loop, `forloop.*`.
- Filtros: `date`, `truncatewords`, `default`, `linebreaks`, `pluralize`,
  `floatformat`... Escaping é automático; `|safe` só em conteúdo confiável.
- Herança com `extends`/`block` (+`block.super`); context processors dão
  variáveis globais; crie custom tags/filtros em `templatetags/`.

Templates exibem dados que vieram do ORM. Domine a busca na
**[QuerySet API completa](querysets-api.md)**.
