"""URL routes for the async blog app.

Async views go into ``path()`` directly, exactly like sync function views — the
async-ness is transparent to the router.
"""

from django.urls import URLPattern, path

from apps.blog import views

app_name = "blog"

urlpatterns: list[URLPattern] = [
    path("", views.post_list, name="post-list"),
    path("posts/<slug:slug>/", views.post_detail, name="post-detail"),
    path("posts/<slug:slug>/comment/", views.comment_create, name="comment-create"),
]
