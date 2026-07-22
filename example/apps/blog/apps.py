from django.apps import AppConfig


class BlogConfig(AppConfig):
    """Application configuration for the blog app.

    The app lives at ``apps/blog`` on disk, so ``name`` uses the dotted import
    path ``apps.blog``. Setting ``label`` to ``blog`` keeps the database table
    names short (``blog_post`` instead of ``apps_blog_post``).
    """

    default_auto_field: str = "django.db.models.BigAutoField"
    name: str = "apps.blog"
    label: str = "blog"
