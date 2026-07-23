"""Admin registration for the async blog (the admin itself runs sync)."""

from django.contrib import admin

from apps.blog.models import Author, Comment, Post, Tag


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Admin configuration for Post."""

    list_display = ["title", "author", "status", "published_at"]
    list_filter = ["status"]
    search_fields = ["title", "body"]
    prepopulated_fields = {"slug": ["title"]}


admin.site.register(Author)
admin.site.register(Tag)
admin.site.register(Comment)
