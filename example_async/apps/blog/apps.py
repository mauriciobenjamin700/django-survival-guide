from django.apps import AppConfig


class BlogConfig(AppConfig):
    """Application configuration for the async blog app."""

    default_auto_field: str = "django.db.models.BigAutoField"
    name: str = "apps.blog"
    label: str = "blog"
