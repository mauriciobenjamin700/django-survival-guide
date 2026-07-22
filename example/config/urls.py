"""Root URL configuration.

Maps top-level URL prefixes to each app's URLconf. Business URLs live under
the app namespaces (``blog:``); Django's built-in auth views provide login and
logout, and the admin site is mounted at ``/admin/``.
"""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import URLPattern, URLResolver, include, path

urlpatterns: list[URLPattern | URLResolver] = [
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("api/", include("apps.blog.api.urls", namespace="blog-api")),
    path("", include("apps.blog.urls", namespace="blog")),
]
