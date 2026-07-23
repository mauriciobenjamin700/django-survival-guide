# Referência: views baseadas em função (FBV)

Este guia prefere [views baseadas em classe](views-cbv.md), mas o Django suporta
os dois estilos — e muita gente **prefere funções**: são explícitas, lineares e
fáceis de ler de cima a baixo. Esta página mostra o mesmo blog no estilo FBV.

!!! quote "Pensa como criança 🧒"
    Uma view de classe é um eletrodoméstico com botões prontos que você regula. Uma
    view de **função** é uma receita escrita à mão: você lê linha por linha, do
    começo ao fim, e vê **exatamente** o que acontece. Nada escondido — o que está
    escrito é o que roda.

## Caso de uso

Uma função de view recebe o `request` e devolve uma resposta. Você decide tudo:

```python
# apps/blog/views.py
from django.shortcuts import get_object_or_404, render
from django.http import HttpRequest, HttpResponse

from apps.blog.models import Post


def post_list(request: HttpRequest) -> HttpResponse:
    """Show the list of published posts."""
    posts = Post.objects.published().select_related("author")
    return render(request, "blog/post_list.html", {"posts": posts})


def post_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """Show a single published post."""
    post = get_object_or_404(Post.objects.published(), slug=slug)
    return render(request, "blog/post_detail.html", {"post": post})
```

```python
# apps/blog/urls.py — sem .as_view(): a função vai direto
urlpatterns = [
    path("", views.post_list, name="post-list"),
    path("posts/<slug:slug>/", views.post_detail, name="post-detail"),
]
```

!!! info "No `urls.py`, FBV é mais direta"
    A CBV precisa de `PostListView.as_view()`; a FBV vai **direto** (`views.post_list`),
    porque ela já é a função que o roteador espera.

## Possibilidades

### As ferramentas do dia a dia

| Ferramenta | Faz |
| --- | --- |
| `render(request, template, context)` | Renderiza um template numa resposta |
| `redirect("nome" ou obj)` | Redireciona (301/302) |
| `get_object_or_404(qs, **kw)` | Busca um objeto ou levanta 404 |
| `get_list_or_404(qs, **kw)` | Lista ou 404 se vazia |
| `HttpResponse` / `JsonResponse` | Resposta crua / JSON |
| `request.method` / `request.POST` / `request.GET` | Dados da requisição |

### Tratando GET e POST na mesma view

Numa FBV, você ramifica pelo método **explicitamente** — o que a CBV faz por
métodos separados:

```python
from django.shortcuts import redirect

from apps.blog.forms import PostForm


def post_create(request: HttpRequest) -> HttpResponse:
    """Create a post: show the form on GET, save it on POST."""
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user.author_profile
            post.save()
            form.save_m2m()                      # (1)!
            return redirect(post.get_absolute_url())
    else:
        form = PostForm()
    return render(request, "blog/post_form.html", {"form": form})
```

1. `commit=False` adia o salvamento para setar o autor; `save_m2m()` grava as
    relações M2M (tags) depois — a CBV cuida disso nos bastidores.

!!! tip "O padrão clássico da FBV"
    `if request.method == "POST":` valida e age; o `else` mostra o formulário
    vazio. Um único `render` no fim serve tanto o GET quanto o POST inválido (com
    erros). É verboso, mas você **vê** o fluxo inteiro.

### Decoradores: o equivalente aos mixins

O que os mixins fazem para CBV, os **decoradores** fazem para FBV:

```python
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods


@login_required
@require_http_methods(["GET", "POST"])       # (1)!
def post_create(request: HttpRequest) -> HttpResponse:
    ...


@permission_required("blog.delete_post")
def post_delete(request: HttpRequest, slug: str) -> HttpResponse:
    ...
```

1. Restringe os métodos aceitos — POST numa rota só-GET vira 405.

| Decorador | Equivale ao mixin |
| --- | --- |
| `@login_required` | `LoginRequiredMixin` |
| `@permission_required("app.perm")` | `PermissionRequiredMixin` |
| `@user_passes_test(fn)` | `UserPassesTestMixin` |
| `@require_http_methods([...])` / `@require_POST` | `http_method_names` |
| `@cache_page(60)` | (cache da view) |

!!! warning "A ordem dos decoradores importa"
    Decoradores aplicam de baixo para cima (o mais próximo da função primeiro).
    Ponha `@login_required` no topo para barrar antes de qualquer outra coisa.

### FBV no DRF: `@api_view`

O DRF também tem o estilo função:

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from apps.blog.api.serializers import PostSerializer


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticatedOrReadOnly])
def posts(request):
    """List posts (GET) or create one (POST)."""
    if request.method == "POST":
        serializer = PostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user.author_profile)
        return Response(serializer.data, status=201)
    qs = Post.objects.published()
    return Response(PostSerializer(qs, many=True).data)
```

## FBV × CBV: quando usar cada uma

| | FBV (função) | CBV (classe) |
| --- | --- | --- |
| Leitura | Linear, tudo à vista | Espalhada em métodos/herança |
| Reuso | Copiar/colar ou helpers | Herança e mixins |
| CRUD repetitivo | Verboso | Enxuto (generic views) |
| Lógica única/atípica | Ótima | Pode "brigar" com o fluxo pronto |
| Curva de aprendizado | Menor | Maior (MRO, ganchos) |

!!! tip "Não é religião — misture"
    Use **CBV** para o CRUD repetitivo (list/detail/create/update/delete), onde as
    generic views economizam muito. Use **FBV** para views únicas, com fluxo
    atípico, ou quando a clareza linear vale mais que o reuso. Um projeto saudável
    tem os dois. Escolha por legibilidade, não por dogma.

## Recapitulando

- Uma FBV recebe `request` e devolve resposta; no `urls.py` vai direto (sem
  `.as_view()`).
- Ferramentas: `render`, `redirect`, `get_object_or_404`, `request.method/POST/GET`.
- Trate GET/POST com `if request.method == "POST":`; `commit=False` + `save_m2m()`
  no create.
- **Decoradores** substituem mixins (`@login_required`, `@require_POST`,
  `@permission_required`); ordem importa.
- DRF tem `@api_view`. Escolha FBV×CBV por **legibilidade e reuso**, e misture.

!!! quote "📖 Na documentação oficial"
    - [Escrevendo views (Django)](https://docs.djangoproject.com/en/stable/topics/http/views/)
    - [View decorators (Django)](https://docs.djangoproject.com/en/stable/topics/http/decorators/)

Para o estilo orientado a objetos, veja [views baseadas em classe](views-cbv.md).
