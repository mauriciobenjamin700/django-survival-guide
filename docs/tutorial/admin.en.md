# Django Admin

Django ships with a complete **admin panel**, generated automatically from
your models. It's one of the biggest time-savers: ready-made
CRUD to manage data, without writing any screens.

!!! quote "Why this matters"
    While you develop, you need to create/edit data all the time. The admin gives
    you that for free — and, with a little object-oriented configuration, it becomes
    a real operations tool.

## Accessing it

Create a superuser and go to `/admin/`:

```bash
uv run python manage.py createsuperuser
```

## Registering models

For a model to appear in the admin, it must be **registered**. Each model
gets a `ModelAdmin` class that describes *how* it appears — keeping the configuration class
next to the model it controls, via a decorator:

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

What each option does:

| Option | Effect |
| --- | --- |
| `list_display` | Columns in the listing |
| `list_filter` | Filters in the sidebar |
| `search_fields` | Search box across those fields |
| `prepopulated_fields` | Generates the `slug` as you type the title |
| `autocomplete_fields` | A search field instead of a giant dropdown |
| `date_hierarchy` | Date navigation at the top |

!!! tip "`@admin.register` vs `admin.site.register`"
    Both forms work. We prefer the **decorator** `@admin.register(Post)`
    because it keeps the admin class and the model it manages visually
    together — more object-oriented and easier to read.

## Inlines: edit relations on the same screen

Comments belong to a post. With an **inline**, you edit them right on the post's
page:

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

1. Now the post's screen shows its comments right below.

## Bulk actions

We need to approve comments. A **custom action** appears in the listing's actions
dropdown and operates on the selected items:

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

!!! note "`queryset.update()` is efficient"
    `queryset.update(is_approved=True)` runs a **single** `UPDATE` in the database for
    all selected rows — it doesn't load object by object. We'll come back to
    this in [QuerySets](querysets.md).

## Recap

- The admin is automatic CRUD from your models — a huge time-saver.
- Register with the `@admin.register` decorator + a `ModelAdmin` class.
- `list_display`, `list_filter`, `search_fields`, etc. shape the interface.
- **Inlines** edit relations on the same screen; **actions** do bulk operations.

The admin is great for *us*. But the public site needs our own screens.
Before building them, let's master how to fetch data: the
**[QuerySets](querysets.md)**.
