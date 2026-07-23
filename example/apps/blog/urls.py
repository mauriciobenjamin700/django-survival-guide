"""URL routes for the blog app.

``app_name`` declares the ``blog`` namespace so URLs are reversed as
``blog:post-detail`` and never collide with routes from other apps. Each route
points at a class-based view via ``.as_view()``.
"""

from django.urls import URLPattern, path

from apps.blog import views

app_name = "blog"

urlpatterns: list[URLPattern] = [
    path("", views.PostListView.as_view(), name="post-list"),
    path("posts/new/", views.PostCreateView.as_view(), name="post-create"),
    path("posts/<slug:slug>/", views.PostDetailView.as_view(), name="post-detail"),
    path("posts/<slug:slug>/edit/", views.PostUpdateView.as_view(), name="post-update"),
    path(
        "posts/<slug:slug>/delete/", views.PostDeleteView.as_view(), name="post-delete"
    ),
    path(
        "posts/<slug:slug>/comment/",
        views.CommentCreateView.as_view(),
        name="comment-create",
    ),
]
