"""Admin site registration for the blog.

Each model gets a dedicated ``ModelAdmin`` subclass configuring how it appears
in Django's built-in admin. Registration uses the ``@admin.register`` decorator
so the admin class and the model it manages stay next to each other.
"""

from django.contrib import admin

from apps.blog.models import Author, Comment, Post, Tag


class CommentInline(admin.TabularInline):
    """Edit a post's comments inline on the post change page."""

    model = Comment
    extra = 0
    fields = ["author_name", "email", "body", "is_approved", "created_at"]
    readonly_fields = ["created_at"]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Admin configuration for :class:`~apps.blog.models.Post`."""

    list_display = ["title", "author", "status", "published_at"]
    list_filter = ["status", "tags", "created_at"]
    search_fields = ["title", "body"]
    prepopulated_fields = {"slug": ["title"]}
    autocomplete_fields = ["author", "tags"]
    date_hierarchy = "published_at"
    inlines = [CommentInline]


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    """Admin configuration for :class:`~apps.blog.models.Author`."""

    list_display = ["display_name", "user", "website"]
    search_fields = ["display_name", "user__username"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin configuration for :class:`~apps.blog.models.Tag`."""

    list_display = ["name", "slug"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin configuration for :class:`~apps.blog.models.Comment`."""

    list_display = ["author_name", "post", "is_approved", "created_at"]
    list_filter = ["is_approved", "created_at"]
    search_fields = ["author_name", "body"]
    actions = ["approve_comments"]

    @admin.action(description="Approve selected comments")
    def approve_comments(self, request: object, queryset: object) -> None:
        """Bulk-approve the comments selected in the changelist.

        Args:
            request: The current admin request.
            queryset: The set of comments selected by the admin user.
        """
        queryset.update(is_approved=True)
