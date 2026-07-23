# Reference: the admin (`ModelAdmin`)

!!! quote "Think like a child 🧒"
    The **admin** is the control panel of a remote-control toy that came ready in
    the box. You didn't build the buttons — they already exist. You just choose
    *which* buttons show up and what each one does. The `ModelAdmin` is the sheet
    of stickers: you stick them on to say "show this little column", "put a filter
    here", "this button approves everything at once".

## Use case

You want to manage posts without writing a single screen: list them with useful
columns, filter by status, search by title, and generate the slug as you type.
Register the model with a `ModelAdmin`:

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

Visit `/admin/`, create a superuser (`python manage.py createsuperuser`), and the
full CRUD is right there. Now **all the stickers** you have available.

## Possibilities

### The listing (changelist)

The screen that lists the objects. The most-used buttons:

| Option | What it does |
| --- | --- |
| `list_display` | Columns shown in the table |
| `list_display_links` | Which columns become an edit link |
| `list_filter` | Filters in the sidebar |
| `search_fields` | Fields scanned by the search box |
| `list_editable` | Fields editable directly in the list |
| `list_per_page` | How many items per page (default 100) |
| `ordering` | Default ordering of the list |
| `date_hierarchy` | Date navigation at the top |
| `list_select_related` | Runs `select_related` on the list (avoids N+1) |
| `actions` | Available bulk actions |
| `empty_value_display` | Text for empty values (e.g. `"—"`) |

!!! tip "`search_fields` crosses relations"
    You can search across related models' fields with `__`:
    ```python
    search_fields = ["title", "author__display_name", "author__user__email"]
    ```

### Computed columns in `list_display`

Think like a child: besides the real drawers, you can invent a "make-believe
column" that shows whatever you want — a method:

```python
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "comment_count", "is_live"]

    @admin.display(description="Comments", ordering="comments__count")
    def comment_count(self, obj: Post) -> int:
        """Show how many comments the post has."""
        return obj.comments.count()

    @admin.display(boolean=True, description="Live?")
    def is_live(self, obj: Post) -> bool:
        """Show a green/red icon for published state."""
        return obj.is_published
```

| `@admin.display(...)` | Effect |
| --- | --- |
| `description` | Column title |
| `ordering` | Makes the column sortable by that field |
| `boolean=True` | Shows a ✓/✗ icon instead of text |

### The edit form (change form)

| Option | What it does |
| --- | --- |
| `fields` | Order/selection of the fields in the form |
| `exclude` | Fields to hide |
| `fieldsets` | Groups fields into sections with titles |
| `readonly_fields` | Read-only fields |
| `prepopulated_fields` | Fills one field from another (slug ← title) |
| `autocomplete_fields` | A search box instead of a giant dropdown |
| `raw_id_fields` | Just the id + a magnifier (for huge relations) |
| `filter_horizontal` / `filter_vertical` | A dual selector for M2M |
| `save_on_top` | Save buttons at the top too |

```python
fieldsets = [
    ("Content", {"fields": ["title", "slug", "body"]}),
    ("Publishing", {
        "fields": ["status", "published_at", "tags"],
        "classes": ["collapse"],          # collapsible section
    }),
]
```

!!! warning "`autocomplete_fields` requires `search_fields` on the target"
    For `autocomplete_fields = ["author"]` to work, the `AuthorAdmin` needs
    `search_fields` defined — that's what the autocomplete searches through.

### Inlines: edit children on the parent's screen

```python
class CommentInline(admin.TabularInline):     # or admin.StackedInline
    """Edit a post's comments on the post page."""

    model = Comment
    extra = 0                    # number of extra blank forms
    readonly_fields = ["created_at"]
    can_delete = True


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    inlines = [CommentInline]
```

| Type | Layout |
| --- | --- |
| `TabularInline` | In table rows (compact) |
| `StackedInline` | One block per object (roomy) |

### Bulk actions

Think like a child: you check several toys and press **one** button that does the
same thing to all of them.

```python
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    actions = ["approve_comments"]

    @admin.action(description="Approve selected comments")
    def approve_comments(self, request, queryset) -> None:
        """Bulk-approve selected comments in one UPDATE."""
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} comments approved.")
```

!!! tip "`queryset.update()` is a single query"
    The action receives a **queryset** with the checked items. `queryset.update(...)`
    runs a single `UPDATE` in the database — it doesn't load object by object. Fast.

### Controlling the queryset and permissions

Override methods for fine-grained rules:

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

| Method | Controls |
| --- | --- |
| `get_queryset(request)` | What shows up in the list |
| `has_add_permission(request)` | Can add? |
| `has_change_permission(request, obj)` | Can edit? |
| `has_delete_permission(request, obj)` | Can delete? |
| `has_view_permission(request, obj)` | Can view? |
| `save_model(request, obj, form, change)` | Acts on save |

### Customizing the admin site

```python
admin.site.site_header = "Blog — Administration"
admin.site.site_title = "Blog Admin"
admin.site.index_title = "Dashboard"
```

!!! quote "📖 In the official docs"
    - [The Django admin site](https://docs.djangoproject.com/en/stable/ref/contrib/admin/)

## Recap

- The admin is a ready-made CRUD; the `ModelAdmin` picks the buttons.
- **Listing**: `list_display`, `list_filter`, `search_fields` (crosses `__`),
  `list_select_related` against N+1.
- Computed columns via a method + `@admin.display`.
- **Editing**: `fieldsets`, `readonly_fields`, `prepopulated_fields`,
  `autocomplete_fields` (requires `search_fields` on the target).
- **Inlines** edit children on the parent's screen; **actions** operate in bulk
  (`queryset.update`).
- Override `get_queryset`/`has_*_permission` for access rules.

Next: how addresses reach the views — **[URLs and converters](urls.md)**.
