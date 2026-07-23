# Referência: motores de template (DTL × Jinja2)

!!! quote "Pensa como criança 🧒"
    Um **motor de template** é quem lê o desenho de colorir (o HTML com espaços) e
    preenche com os dados. O Django vem com o seu próprio pintor — a **DTL**
    (Django Template Language) — mas aceita contratar outro pintor famoso, o
    **Jinja2**. Os dois pintam o mesmo quadro; mudam o jeito de segurar o pincel
    (a sintaxe) e a velocidade.

## Caso de uso

Você quer saber **qual** motor está renderizando suas páginas e como o Django o
encontra. Tudo mora no setting `TEMPLATES`, que é uma **lista** — cada item é um
motor:

```python
# config/settings.py
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",  # (1)!
        "DIRS": [BASE_DIR / "templates"],                              # (2)!
        "APP_DIRS": True,                                              # (3)!
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
```

1. O **motor**: aqui, a DTL. Trocar essa string troca o pintor.
2. Pastas de templates do projeto (fora dos apps).
3. `True` = também procura em `<app>/templates/` de cada app instalado.

## Possibilidades

### DTL × Jinja2: quando usar cada um

| | DTL (padrão) | Jinja2 |
| --- | --- | --- |
| Vem no Django | ✅ Sim | Precisa instalar (`jinja2`) |
| Filosofia | Limitada de propósito (pouca lógica no template) | Mais poderosa (permite mais Python) |
| `{% url %}`, `{% csrf_token %}` | Nativos | Precisam ser expostos manualmente |
| Admin, auth, DRF browsable | Usam DTL | — |
| Velocidade | Boa | Geralmente mais rápida |

!!! tip "Regra prática: fique na DTL"
    Para 95% dos projetos, a **DTL** é a escolha certa — é o padrão, integra com
    admin/auth/mensagens e força a manter lógica fora do template (o que é bom).
    Considere **Jinja2** só quando você precisa de expressões mais ricas no
    template, ou já vem de outro ecossistema Python que usa Jinja2.

!!! info "Dá para usar os dois ao mesmo tempo"
    `TEMPLATES` é uma lista: você pode registrar DTL **e** Jinja2 juntos. O Django
    tenta cada motor na ordem até um deles achar o template. Na prática, separe
    por pasta/extensão para não confundir.

### Configurando o Jinja2

```python
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [BASE_DIR / "jinja2"],
        "APP_DIRS": True,
        "OPTIONS": {
            "environment": "config.jinja2.environment",   # (1)!
        },
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["..."]},
    },
]
```

1. Uma função que monta o `Environment` do Jinja2. É onde você **reexpõe** o que
    a DTL dá de graça (`static`, `url`):

```python
# config/jinja2.py
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment


def environment(**options) -> Environment:
    """Build a Jinja2 environment exposing Django's static() and url()."""
    env = Environment(**options)
    env.globals.update({"static": static, "url": reverse})
    return env
```

!!! warning "No Jinja2 você perde os atalhos da DTL"
    `{% url %}`, `{% static %}`, `{% csrf_token %}`, filtros do Django — nada
    disso existe no Jinja2 por padrão. Você reexpõe manualmente no
    `environment` (como acima). Esquecer disso é a dor de cabeça nº 1 de quem
    migra.

### Sintaxe lado a lado

=== "DTL"

    ```django
    {% for post in posts %}
      <a href="{% url 'blog:post-detail' post.slug %}">{{ post.title|upper }}</a>
    {% empty %}
      <p>Sem posts.</p>
    {% endfor %}
    ```

=== "Jinja2"

    ```jinja
    {% for post in posts %}
      <a href="{{ url('blog:post-detail', slug=post.slug) }}">{{ post.title|upper }}</a>
    {% else %}
      <p>Sem posts.</p>
    {% endfor %}
    ```

Diferenças-chave: no Jinja2 as tags viram **chamadas de função** (`url(...)`), o
caso-vazio é `{% else %}` (não `{% empty %}`), e você pode chamar métodos com
parênteses.

### Como o Django acha o template: loaders

Dentro da DTL, os **loaders** definem *onde* e *como* procurar os arquivos:

| Loader | O que faz |
| --- | --- |
| `app_directories` | Procura em `<app>/templates/` (ligado por `APP_DIRS: True`) |
| `filesystem` | Procura nas pastas de `DIRS` |
| `cached` | Embrulha os outros e **guarda em memória** o template compilado |

!!! tip "O cached loader em produção"
    Por padrão, com `APP_DIRS: True` o Django já usa `app_directories` +
    `filesystem`. Em produção, o **cached loader** compila cada template uma vez
    e reusa — ganho real de performance. Configure-o explicitamente em `OPTIONS`
    com `loaders` quando quiser controlar isso (não combine `loaders` com
    `APP_DIRS` no mesmo motor).

### Onde os templates ficam (recap do finder)

- `templates/` na raiz do projeto (via `DIRS`).
- `<app>/templates/<app>/` em cada app (via `APP_DIRS`), com o subdiretório
  homônimo criando o namespace (`blog/post_list.html`).

Para o conteúdo da DTL em si — tags, filtros, herança — veja
**[Templates](templates.md)**.

!!! quote "📖 Na documentação oficial"
    - [Templates](https://docs.djangoproject.com/en/stable/topics/templates/)
    - [The templates API (backends)](https://docs.djangoproject.com/en/stable/ref/templates/api/)

## Recap

- Um **motor de template** renderiza o HTML; o setting `TEMPLATES` é uma lista de
  motores, cada um com seu `BACKEND`.
- **DTL** (padrão, integra tudo, lógica limitada de propósito) × **Jinja2**
  (mais poderoso e rápido, mas você reexpõe `url`/`static`/`csrf` na mão).
- Dá para usar os dois; o Django tenta na ordem.
- **Loaders** (`app_directories`, `filesystem`, `cached`) definem onde/como achar
  os arquivos; `APP_DIRS: True` liga a busca nos apps; o `cached` acelera em
  produção.
- Regra prática: fique na DTL salvo motivo forte.

Para a linguagem da DTL em detalhe, siga para **[Templates](templates.md)**.
