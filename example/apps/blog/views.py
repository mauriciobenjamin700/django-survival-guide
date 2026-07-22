"""Class-based views for the blog.

Every view here is a class. Django's generic views encapsulate the common
request/response patterns (list, detail, create, update, delete) as methods you
override instead of ``if request.method == ...`` branches. Mixins add
orthogonal behaviour — for example :class:`LoginRequiredMixin` gates a view
behind authentication without touching its core logic.
"""

from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from apps.blog.forms import CommentForm, PostForm
from apps.blog.models import Post, Tag


class PostListView(ListView):
    """Paginated list of published posts, optionally filtered by tag."""

    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 5

    def get_queryset(self) -> QuerySet[Post]:
        """Return published posts, narrowed by the optional ``tag`` query.

        Returns:
            Published posts, filtered to a single tag when a ``tag`` slug is
            present in the query string.
        """
        tag_slug = self.request.GET.get("tag")
        if tag_slug:
            return Post.objects.by_tag(tag_slug).select_related("author")
        return Post.objects.published().select_related("author")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add the tag list and the active tag to the template context.

        Args:
            **kwargs: Base context provided by ``ListView``.

        Returns:
            The context dictionary extended with ``tags`` and ``active_tag``.
        """
        context = super().get_context_data(**kwargs)
        context["tags"] = Tag.objects.all()
        context["active_tag"] = self.request.GET.get("tag", "")
        return context


class PostDetailView(DetailView):
    """Detail page for a single published post, plus its comment form."""

    template_name = "blog/post_detail.html"
    context_object_name = "post"

    def get_queryset(self) -> QuerySet[Post]:
        """Return the published posts a visitor is allowed to view.

        Returns:
            The published posts queryset with the author preloaded.
        """
        return Post.objects.published().select_related("author")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add approved comments and an empty comment form to the context.

        Args:
            **kwargs: Base context provided by ``DetailView``.

        Returns:
            The context dictionary extended with ``comments`` and ``form``.
        """
        context = super().get_context_data(**kwargs)
        context["comments"] = self.object.approved_comments()
        context["form"] = CommentForm()
        return context


class CommentCreateView(CreateView):
    """Handle the POST that creates a comment for a given post."""

    form_class = CommentForm
    http_method_names = ["post"]

    def form_valid(self, form: CommentForm) -> HttpResponse:
        """Attach the new comment to its post before saving.

        Args:
            form: The validated comment form.

        Returns:
            A redirect to the parent post's detail page.
        """
        post = get_object_or_404(Post.objects.published(), slug=self.kwargs["slug"])
        form.instance.post = post
        form.save()
        return HttpResponseRedirect(post.get_absolute_url())


class AuthorPostMixin(LoginRequiredMixin):
    """Shared configuration for views that create or edit posts.

    Centralises the model, form class and success behaviour so the concrete
    create/update views stay a couple of lines each.
    """

    model = Post
    form_class = PostForm
    template_name = "blog/post_form.html"

    def get_success_url(self) -> str:
        """Return the URL to redirect to after a successful save.

        Returns:
            The saved post's detail page URL.
        """
        return self.object.get_absolute_url()


class PostCreateView(AuthorPostMixin, CreateView):
    """Create a new post authored by the current user."""

    def form_valid(self, form: PostForm) -> HttpResponse:
        """Set the post's author to the logged-in user before saving.

        Args:
            form: The validated post form.

        Returns:
            The response produced by the parent ``form_valid``.
        """
        form.instance.author = self.request.user.author_profile
        return super().form_valid(form)


class PostUpdateView(AuthorPostMixin, UpdateView):
    """Edit an existing post."""

    slug_url_kwarg = "slug"


class PostDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a post after a confirmation step."""

    model = Post
    slug_url_kwarg = "slug"
    template_name = "blog/post_confirm_delete.html"
    success_url = reverse_lazy("blog:post-list")
