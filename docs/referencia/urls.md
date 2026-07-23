# Referência: URLs e conversores

!!! quote "Pensa como criança 🧒"
    A URL é o **endereço da casa**. O `urls.py` é o carteiro: ele olha o endereço
    escrito no envelope (o que você digita no navegador) e sabe em qual porta
    (qual view) entregar. Um **conversor** é o carteiro conferindo o formato:
    "esse pedaço tem que ser um número", "esse tem que ser um nome com hífens".

## Caso de uso

Você quer que `/posts/ola-mundo/` mostre o post de slug `ola-mundo`, e que
`/posts/42/` não seja aceito como slug. Você mapeia a rota, captura o pedaço
variável com um conversor, e ele chega na view:

```python
# apps/blog/urls.py
from django.urls import URLPattern, path

from apps.blog import views

app_name = "blog"

urlpatterns: list[URLPattern] = [
    path("", views.PostListView.as_view(), name="post-list"),
    path("posts/<slug:slug>/", views.PostDetailView.as_view(), name="post-detail"),
]
```

O `<slug:slug>` captura `ola-mundo` e entrega para a view em
`self.kwargs["slug"]`. Vamos ver todas as peças.

## Possibilidades

### `path()` vs `re_path()`

| Função | Como casa a rota |
| --- | --- |
| `path()` | Sintaxe simples com conversores `<tipo:nome>` (use quase sempre) |
| `re_path()` | Expressão regular (para padrões que `path` não expressa) |

```python
from django.urls import path, re_path

path("posts/<int:year>/<slug:slug>/", view)             # simples
re_path(r"^posts/(?P<year>[0-9]{4})/$", view)           # regex
```

### Conversores embutidos

| Conversor | Casa com | Exemplo de valor |
| --- | --- | --- |
| `str` | Texto sem `/` (padrão se você omitir o tipo) | `ola-mundo` |
| `int` | Inteiros ≥ 0 | `42` |
| `slug` | Letras, números, hífen e underscore | `meu-post-1` |
| `uuid` | UUID formatado | `075194d3-...` |
| `path` | Texto **incluindo** `/` (pega o resto) | `docs/guia/intro` |

```python
path("artigo/<uuid:id>/", view)
path("arquivo/<path:caminho>/", view)   # caminho pode ter barras
```

!!! tip "Sem tipo = `str`"
    `<slug>` é atalho para `<str:slug>`? Não — `<slug>` usa o conversor `str`
    com o **nome** `slug`. Para usar o conversor slug de verdade, escreva o tipo:
    `<slug:slug>`. O primeiro pedaço é o **tipo**, o segundo é o **nome** do
    argumento.

### A ordem importa (muito)

```python
urlpatterns = [
    path("posts/new/", views.PostCreateView.as_view(), name="post-create"),
    path("posts/<slug:slug>/", views.PostDetailView.as_view(), name="post-detail"),
]
```

!!! danger "Específico antes de genérico"
    O Django testa de cima para baixo e **para na primeira** que casa. Se
    `<slug:slug>` viesse antes, `/posts/new/` seria capturado como um post de
    slug `"new"`. Sempre ponha rotas específicas antes das que têm variável.
    Pensa como criança: procure a chave exata antes da chave-mestra.

### `include()`: dividir por app

O `urls.py` raiz delega prefixos inteiros para cada app:

```python
# config/urls.py
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.blog.api.urls", namespace="blog-api")),
    path("", include("apps.blog.urls", namespace="blog")),
]
```

Pensa como criança: o carteiro-chefe vê o **bairro** (`api/`) e passa o envelope
para o carteiro daquele bairro, que cuida das ruas de lá.

!!! warning "Passou `namespace=`? O módulo incluído precisa de `app_name`"
    `include("apps.blog.urls", namespace="blog")` só funciona se
    `apps/blog/urls.py` definir `app_name = "blog"`. Sem isso, o Django levanta
    `ImproperlyConfigured: Specifying a namespace in include() without providing
    an app_name is not supported`.

### Namespaces: nomes sem colisão

Dois apps podem ter uma rota `post-list`. O namespace desambigua:

```python
# no urls.py do app
app_name = "blog"                    # define o namespace

# ao referenciar, use namespace:nome
reverse("blog:post-detail", kwargs={"slug": "ola-mundo"})
```

### Reverse: nunca escreva URL na mão

Pensa como criança: em vez de decorar o número da casa, você chama a pessoa pelo
**nome** e alguém te leva até lá. Se a casa mudar de rua, o nome continua valendo.

=== "No Python"

    ```python
    from django.urls import reverse, reverse_lazy

    reverse("blog:post-detail", kwargs={"slug": "ola-mundo"})   # "/posts/ola-mundo/"
    reverse_lazy("blog:post-list")   # em atributos de classe (avaliação adiada)
    ```

=== "No template"

    ```django
    <a href="{% url 'blog:post-detail' post.slug %}">{{ post.title }}</a>
    ```

=== "No modelo"

    ```python
    def get_absolute_url(self) -> str:
        return reverse("blog:post-detail", kwargs={"slug": self.slug})
    ```

| Função | Use quando |
| --- | --- |
| `reverse()` | Dentro de métodos/funções (avaliado na hora) |
| `reverse_lazy()` | Em atributos de classe / settings (avaliação adiada) |
| `{% url %}` | Em templates |

!!! warning "`reverse_lazy` em atributo de classe"
    Atributos de classe (`success_url = ...`) são avaliados quando o módulo é
    **importado** — cedo demais, as URLs podem não estar carregadas. Use
    `reverse_lazy` ali; `reverse` normal dentro de métodos.

### Passando argumentos extras

```python
path("posts/<slug:slug>/", views.PostDetailView.as_view(),
     kwargs={"template": "amp"}, name="post-detail-amp")
```

!!! quote "📖 Na documentação oficial"
    - [URL dispatcher](https://docs.djangoproject.com/en/stable/topics/http/urls/)

## Recap

- `path()` (simples, quase sempre) × `re_path()` (regex).
- Conversores: `str` (padrão), `int`, `slug`, `uuid`, `path` (aceita `/`).
  Sintaxe `<tipo:nome>`.
- Ordem importa: **específico antes de genérico**; o Django para na 1ª que casa.
- `include()` divide por app; `app_name` cria o **namespace** (`blog:post-list`).
- Sempre referencie por **nome**: `reverse`/`reverse_lazy`/`{% url %}` — nunca
  URL literal.

Da URL você chega na view, que devolve HTML pelos **[templates](templates.md)**.
