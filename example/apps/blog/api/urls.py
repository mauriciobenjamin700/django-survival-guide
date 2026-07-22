"""API URL routes for the blog.

A DRF ``DefaultRouter`` inspects each registered viewset and generates the full
set of REST routes (list, detail, create, update, delete) plus a browsable API
root. The generated patterns live under the ``blog-api`` namespace.
"""

from django.urls import URLResolver, include, path
from rest_framework.routers import DefaultRouter

from apps.blog.api.views import CommentViewSet, PostViewSet, TagViewSet

app_name = "blog-api"

router = DefaultRouter()
router.register("posts", PostViewSet, basename="post")
router.register("tags", TagViewSet, basename="tag")
router.register("comments", CommentViewSet, basename="comment")

urlpatterns: list[URLResolver] = [
    path("", include(router.urls)),
]
