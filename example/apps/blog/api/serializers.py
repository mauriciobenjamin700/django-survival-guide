"""DRF serializers for the blog.

Serializers are to a REST API what forms/templates are to HTML: they validate
incoming JSON and render model instances as JSON. ``ModelSerializer`` derives
fields from the model, exactly like ``ModelForm`` does for forms.
"""

from rest_framework import serializers

from apps.blog.models import Author, Comment, Post, Tag


class TagSerializer(serializers.ModelSerializer):
    """Serialize a :class:`~apps.blog.models.Tag`."""

    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class AuthorSerializer(serializers.ModelSerializer):
    """Serialize an :class:`~apps.blog.models.Author` profile."""

    class Meta:
        model = Author
        fields = ["id", "display_name", "bio", "website"]


class CommentSerializer(serializers.ModelSerializer):
    """Serialize a :class:`~apps.blog.models.Comment`.

    ``is_approved`` and ``created_at`` are read-only: readers submit content,
    moderation state is controlled server-side.
    """

    class Meta:
        model = Comment
        fields = [
            "id",
            "post",
            "author_name",
            "email",
            "body",
            "is_approved",
            "created_at",
        ]
        read_only_fields = ["is_approved", "created_at"]


class PostSerializer(serializers.ModelSerializer):
    """Serialize a :class:`~apps.blog.models.Post`.

    Nested read-only representations expose the author and tags as objects,
    while ``tag_ids`` accepts a write-only list of primary keys so clients can
    set tags without sending the full nested payload.
    """

    author = AuthorSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Tag.objects.all(),
        source="tags",
        required=False,
    )

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "slug",
            "author",
            "body",
            "tags",
            "tag_ids",
            "status",
            "published_at",
            "created_at",
        ]
        read_only_fields = ["slug", "published_at", "created_at"]
