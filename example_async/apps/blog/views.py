"""Async views for the blog.

Every view here is an ``async def``. Django runs them on the event loop, so they
can ``await`` I/O — the async ORM (``aget``, ``async for``, ``acreate``) and any
async HTTP calls — without blocking a worker thread.

The key rules:

* Query the ORM with its async API: ``async for`` to iterate, ``aget_object_or_404``
  for a single row, ``acreate``/``asave`` to write.
* Materialize a queryset into a list **before** handing it to a template — the
  template engine iterates synchronously.
* Anything sync-only that touches the DB must be wrapped in ``sync_to_async``.
"""

from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import aget_object_or_404, render

from apps.blog.forms import CommentForm
from apps.blog.models import Comment, Post


async def post_list(request: HttpRequest) -> HttpResponse:
    """List published posts (async).

    Iterates the queryset with ``async for`` and materializes it into a list so
    the template can render it synchronously.
    """
    posts = [post async for post in Post.objects.published().select_related("author")]
    return render(request, "blog/post_list.html", {"posts": posts})


async def post_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """Show one published post and its approved comments (async)."""
    post = await aget_object_or_404(
        Post.objects.published().select_related("author"),
        slug=slug,
    )
    comments = [comment async for comment in post.approved_comments()]
    context = {"post": post, "comments": comments, "form": CommentForm()}
    return render(request, "blog/post_detail.html", context)


async def comment_create(request: HttpRequest, slug: str) -> HttpResponse:
    """Create a comment for a post (async POST handler).

    The form validates synchronously (CPU only); persistence uses the async
    ORM via ``acreate``.
    """
    post = await aget_object_or_404(Post.objects.published(), slug=slug)
    form = CommentForm(request.POST)
    if form.is_valid():
        await Comment.objects.acreate(post=post, **form.cleaned_data)
    return HttpResponseRedirect(post.get_absolute_url())
