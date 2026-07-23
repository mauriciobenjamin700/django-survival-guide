# Admin do Django

O Django vem com um **painel administrativo** completo, gerado automaticamente a
partir dos seus modelos. É uma das funcionalidades que mais economizam tempo:
CRUD pronto para gerenciar dados, sem escrever telas.

!!! quote "Por que isso importa"
    Enquanto você desenvolve, precisa criar/editar dados o tempo todo. O admin te
    dá isso de graça — e, com um pouco de configuração orientada a objetos, vira
    uma ferramenta de operação de verdade.

## Acessando

Crie um superusuário e acesse `/admin/`:

```bash
uv run python manage.py createsuperuser
```

## Registrando modelos

Para um modelo aparecer no admin, ele precisa ser **registrado**. Cada modelo
ganha uma classe `ModelAdmin` que descreve *como* ele aparece — mantendo a classe
de configuração ao lado do modelo que ela controla, via decorador:

```python
from django.contrib import admin

from apps.blog.models import Author, Comment, Post, Tag


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Admin configuration for Post."""

    list_display = ["title", "author", "status", "published_at"]
    list_filter = ["status", "tags", "created_at"]
    search_fields = ["title", "body"]
    prepopulated_fields = {"slug": ["title"]}
    autocomplete_fields = ["author", "tags"]
    date_hierarchy = "published_at"
```

O que cada opção faz:

| Opção | Efeito |
| --- | --- |
| `list_display` | Colunas na listagem |
| `list_filter` | Filtros na barra lateral |
| `search_fields` | Caixa de busca por esses campos |
| `prepopulated_fields` | Gera o `slug` enquanto você digita o título |
| `autocomplete_fields` | Campo de busca em vez de dropdown gigante |
| `date_hierarchy` | Navegação por data no topo |

!!! tip "`@admin.register` vs `admin.site.register`"
    As duas formas funcionam. Preferimos o **decorador** `@admin.register(Post)`
    porque deixa a classe de admin e o modelo que ela gerencia visualmente
    juntos — mais orientado a objetos e fácil de ler.

## Inlines: editar relações na mesma tela

Comentários pertencem a um post. Com um **inline**, você os edita direto na
página do post:

```python
class CommentInline(admin.TabularInline):
    """Edit a post's comments inline on the post change page."""

    model = Comment
    extra = 0
    readonly_fields = ["created_at"]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    inlines = [CommentInline]  # (1)!
    # ... resto da configuração
```

1. Agora a tela de um post mostra seus comentários logo abaixo.

## Ações em massa

Precisamos aprovar comentários. Uma **ação customizada** aparece no dropdown de
ações da listagem e opera sobre os itens selecionados:

```python
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["author_name", "post", "is_approved", "created_at"]
    list_filter = ["is_approved", "created_at"]
    actions = ["approve_comments"]

    @admin.action(description="Approve selected comments")
    def approve_comments(self, request: object, queryset: object) -> None:
        """Bulk-approve the comments selected in the changelist."""
        queryset.update(is_approved=True)
```

!!! note "`queryset.update()` é eficiente"
    `queryset.update(is_approved=True)` faz **um único** `UPDATE` no banco para
    todas as linhas selecionadas — não carrega objeto por objeto. Voltaremos a
    isso em [QuerySets](querysets.md).

!!! quote "📖 Na documentação oficial"
    - [The Django admin site](https://docs.djangoproject.com/en/stable/ref/contrib/admin/)

## Recapitulando

- O admin é um CRUD automático a partir dos modelos — enorme economia de tempo.
- Registre com o decorador `@admin.register` + uma classe `ModelAdmin`.
- `list_display`, `list_filter`, `search_fields` etc. moldam a interface.
- **Inlines** editam relações na mesma tela; **actions** fazem operações em massa.

O admin é ótimo para *nós*. Mas o site público precisa das nossas próprias telas.
Antes de construí-las, vamos dominar como buscar dados: os
**[QuerySets](querysets.md)**.
