"""DRF viewsets for the blog.

A ``ViewSet`` is the API counterpart of Django's class-based views: one class
provides list/retrieve/create/update/destroy actions, and a router turns it
into the full set of REST URLs. This keeps the API layer as object-oriented as
the server-rendered views.
"""

from django.db.models import QuerySet
from rest_framework import viewsets

from apps.blog.api.serializers import CommentSerializer, PostSerializer, TagSerializer
from apps.blog.models import Comment, Post, Tag


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only list/detail endpoints for tags."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class PostViewSet(viewsets.ModelViewSet):
    """Full CRUD API for posts.

    Anonymous clients see only published posts; authenticated clients see
    everything, so authors can manage their drafts through the API.
    """

    serializer_class = PostSerializer
    lookup_field = "slug"

    def get_queryset(self) -> QuerySet[Post]:
        """Return posts visible to the current client.

        Returns:
            All posts for authenticated users, published posts otherwise, with
            the author preloaded to avoid per-row queries.
        """
        base = Post.objects.select_related("author").prefetch_related("tags")
        if self.request.user.is_authenticated:
            return base
        return base.filter(status=Post.Status.PUBLISHED)

    def perform_create(self, serializer: PostSerializer) -> None:
        """Attach the logged-in user's author profile to the new post.

        Args:
            serializer: The validated post serializer ready to be saved.
        """
        serializer.save(author=self.request.user.author_profile)


class CommentViewSet(viewsets.ModelViewSet):
    """CRUD API for comments, filterable by post via ``?post=<id>``."""

    serializer_class = CommentSerializer

    def get_queryset(self) -> QuerySet[Comment]:
        """Return approved comments, optionally filtered by post id.

        Returns:
            Approved comments, narrowed to a single post when the ``post`` query
            parameter is supplied.
        """
        queryset = Comment.objects.filter(is_approved=True)
        post_id = self.request.query_params.get("post")
        if post_id:
            return queryset.filter(post_id=post_id)
        return queryset
