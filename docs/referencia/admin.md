# Referência: o admin (`ModelAdmin`)

!!! quote "Pensa como criança 🧒"
    O **admin** é o painel de controle de um brinquedo de controle remoto que já
    veio pronto na caixa. Você não construiu os botões — eles já existem. Você só
    escolhe *quais* botões aparecem e o que cada um faz. A `ModelAdmin` é a folha
    de adesivos: você cola pra dizer "mostra essa coluninha", "põe um filtro
    aqui", "esse botão aprova tudo de uma vez".

## Caso de uso

Você quer gerenciar posts sem escrever tela nenhuma: listar com colunas úteis,
filtrar por status, buscar por título, e gerar o slug enquanto digita. Registre
o modelo com uma `ModelAdmin`:

```python
# apps/blog/admin.py
from django.contrib import admin

from apps.blog.models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Admin configuration for Post."""

    list_display = ["title", "author", "status", "published_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["title", "body"]
    prepopulated_fields = {"slug": ["title"]}
```

Acesse `/admin/`, crie um superusuário (`python manage.py createsuperuser`), e o
CRUD completo está lá. Agora **todos os adesivos** disponíveis.

## Possibilidades

### A listagem (changelist)

A tela que lista os objetos. Os botões mais usados:

| Opção | O que faz |
| --- | --- |
| `list_display` | Colunas exibidas na tabela |
| `list_display_links` | Quais colunas viram link para editar |
| `list_filter` | Filtros na barra lateral |
| `search_fields` | Campos varridos pela caixa de busca |
| `list_editable` | Campos editáveis direto na lista |
| `list_per_page` | Quantos itens por página (padrão 100) |
| `ordering` | Ordem padrão da lista |
| `date_hierarchy` | Navegação por data no topo |
| `list_select_related` | Faz `select_related` na lista (evita N+1) |
| `actions` | Ações em massa disponíveis |
| `empty_value_display` | Texto para valores vazios (ex.: `"—"`) |

!!! tip "`search_fields` atravessa relações"
    Você pode buscar em campos de modelos relacionados com `__`:
    ```python
    search_fields = ["title", "author__display_name", "author__user__email"]
    ```

### Colunas calculadas em `list_display`

Pensa como criança: além das gavetas reais, você pode inventar uma "coluna de
mentira" que mostra o que quiser — um método:

```python
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "comment_count", "is_live"]

    @admin.display(description="Comentários", ordering="comments__count")
    def comment_count(self, obj: Post) -> int:
        """Show how many comments the post has."""
        return obj.comments.count()

    @admin.display(boolean=True, description="No ar?")
    def is_live(self, obj: Post) -> bool:
        """Show a green/red icon for published state."""
        return obj.is_published
```

| `@admin.display(...)` | Efeito |
| --- | --- |
| `description` | Título da coluna |
| `ordering` | Torna a coluna ordenável por esse campo |
| `boolean=True` | Mostra ícone ✓/✗ em vez de texto |

### O formulário de edição (change form)

| Opção | O que faz |
| --- | --- |
| `fields` | Ordem/seleção dos campos no form |
| `exclude` | Campos a esconder |
| `fieldsets` | Agrupa campos em seções com títulos |
| `readonly_fields` | Campos só de leitura |
| `prepopulated_fields` | Preenche um campo a partir de outro (slug ← título) |
| `autocomplete_fields` | Campo de busca em vez de dropdown gigante |
| `raw_id_fields` | Só o id + lupa (para relações enormes) |
| `filter_horizontal` / `filter_vertical` | Seletor duplo para M2M |
| `save_on_top` | Botões de salvar também no topo |

```python
fieldsets = [
    ("Conteúdo", {"fields": ["title", "slug", "body"]}),
    ("Publicação", {
        "fields": ["status", "published_at", "tags"],
        "classes": ["collapse"],          # seção recolhível
    }),
]
```

!!! warning "`autocomplete_fields` exige `search_fields` no alvo"
    Para `autocomplete_fields = ["author"]` funcionar, o `AuthorAdmin` precisa
    ter `search_fields` definido — é por ali que o autocomplete busca.

### Inlines: editar filhos na tela do pai

```python
class CommentInline(admin.TabularInline):     # ou admin.StackedInline
    """Edit a post's comments on the post page."""

    model = Comment
    extra = 0                    # nº de formulários vazios extras
    readonly_fields = ["created_at"]
    can_delete = True


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    inlines = [CommentInline]
```

| Tipo | Layout |
| --- | --- |
| `TabularInline` | Em linhas de tabela (compacto) |
| `StackedInline` | Um bloco por objeto (espaçoso) |

### Ações em massa

Pensa como criança: você marca vários brinquedos e aperta **um** botão que faz a
mesma coisa com todos.

```python
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    actions = ["approve_comments"]

    @admin.action(description="Aprovar comentários selecionados")
    def approve_comments(self, request, queryset) -> None:
        """Bulk-approve selected comments in one UPDATE."""
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} comentários aprovados.")
```

!!! tip "`queryset.update()` é uma query só"
    A ação recebe um **queryset** com os itens marcados. `queryset.update(...)`
    faz um único `UPDATE` no banco — não carrega objeto por objeto. Rápido.

### Controlando o queryset e as permissões

Sobrescreva métodos para regras finas:

```python
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        """Non-superusers only see their own posts."""
        qs = super().get_queryset(request).select_related("author")
        if request.user.is_superuser:
            return qs
        return qs.filter(author__user=request.user)

    def has_delete_permission(self, request, obj=None) -> bool:
        """Only superusers may delete."""
        return request.user.is_superuser
```

| Método | Controla |
| --- | --- |
| `get_queryset(request)` | O que aparece na lista |
| `has_add_permission(request)` | Pode adicionar? |
| `has_change_permission(request, obj)` | Pode editar? |
| `has_delete_permission(request, obj)` | Pode apagar? |
| `has_view_permission(request, obj)` | Pode ver? |
| `save_model(request, obj, form, change)` | Age ao salvar |

### Customizando o site do admin

```python
admin.site.site_header = "Blog — Administração"
admin.site.site_title = "Blog Admin"
admin.site.index_title = "Painel"
```

!!! quote "📖 Na documentação oficial"
    - [The Django admin site](https://docs.djangoproject.com/en/stable/ref/contrib/admin/)

## Recap

- O admin é um CRUD pronto; a `ModelAdmin` escolhe os botões.
- **Listagem**: `list_display`, `list_filter`, `search_fields` (atravessa `__`),
  `list_select_related` contra N+1.
- Colunas calculadas via método + `@admin.display`.
- **Edição**: `fieldsets`, `readonly_fields`, `prepopulated_fields`,
  `autocomplete_fields` (exige `search_fields` no alvo).
- **Inlines** editam filhos na tela do pai; **actions** operam em massa
  (`queryset.update`).
- Sobrescreva `get_queryset`/`has_*_permission` para regras de acesso.

Próximo: como os endereços chegam nas views — **[URLs e conversores](urls.md)**.
