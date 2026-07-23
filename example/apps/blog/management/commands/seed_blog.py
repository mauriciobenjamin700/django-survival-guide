"""Management command that seeds the blog with demo data.

Run with ``python manage.py seed_blog``. It is idempotent: existing objects are
reused via ``get_or_create`` so running it twice does not duplicate rows. It
creates a demo author (username ``demo`` / password ``demo12345``), a handful of
tags and several published posts with comments, giving a fresh clone something
to render immediately.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.blog.models import Author, Comment, Post, Tag

User = get_user_model()

DEMO_POSTS: list[dict[str, object]] = [
    {
        "title": "Why class-based views scale",
        "body": "Generic views turn request handling into small method overrides.\n"
        "You stop writing branching if/else and start composing behaviour.",
        "tags": ["django", "views"],
    },
    {
        "title": "Typing your Django models",
        "body": "Type hints do not change runtime behaviour, but they make intent\n"
        "explicit and let editors catch mistakes before you run the server.",
        "tags": ["django", "typing"],
    },
    {
        "title": "QuerySets are lazy — use it",
        "body": "A queryset does not hit the database until you iterate it.\n"
        "Chain filters freely and let the ORM build one efficient query.",
        "tags": ["django", "orm"],
    },
    {
        "title": "From templates to DRF",
        "body": "The same models power server-rendered pages and a REST API.\n"
        "DRF serializers play the role templates play for HTML.",
        "tags": ["drf", "api"],
    },
]


class Command(BaseCommand):
    """Populate the database with a demo author, tags, posts and comments."""

    help = "Seed the blog with idempotent demo data."

    @transaction.atomic
    def handle(self, *args: object, **options: object) -> None:
        """Create the demo dataset inside a single transaction.

        Args:
            *args: Unused positional arguments from the command runner.
            **options: Parsed command-line options (none are defined).
        """
        user, created = User.objects.get_or_create(
            username="demo",
            defaults={"email": "demo@example.com"},
        )
        if created:
            user.set_password("demo12345")
            user.save()

        author, _ = Author.objects.get_or_create(
            user=user,
            defaults={"display_name": "Demo Author", "bio": "Writes about Django."},
        )

        for entry in DEMO_POSTS:
            post, created_post = Post.objects.get_or_create(
                title=entry["title"],
                defaults={
                    "author": author,
                    "body": entry["body"],
                    "status": Post.Status.PUBLISHED,
                },
            )
            if created_post:
                tags = [
                    Tag.objects.get_or_create(name=name)[0] for name in entry["tags"]
                ]
                post.tags.set(tags)
                Comment.objects.create(
                    post=post,
                    author_name="Reader",
                    email="reader@example.com",
                    body="Great post, thanks!",
                    is_approved=True,
                )

        self.stdout.write(self.style.SUCCESS("Seeded blog demo data."))
