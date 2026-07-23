"""Seed the async blog with demo data (idempotent).

Management commands run synchronously, so this uses the regular sync ORM — the
async story is about serving requests, not about one-off scripts.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.blog.models import Author, Comment, Post

User = get_user_model()


class Command(BaseCommand):
    """Populate the database with a demo author, posts and comments."""

    help = "Seed the async blog with idempotent demo data."

    @transaction.atomic
    def handle(self, *args: object, **options: object) -> None:
        """Create the demo dataset inside a single transaction."""
        user, created = User.objects.get_or_create(
            username="demo",
            defaults={"email": "demo@example.com"},
        )
        if created:
            user.set_password("demo12345")
            user.save()

        author, _ = Author.objects.get_or_create(
            user=user,
            defaults={"display_name": "Demo Author"},
        )

        for i in range(1, 4):
            post, made = Post.objects.get_or_create(
                title=f"Async post {i}",
                defaults={
                    "author": author,
                    "body": "Served by an async view using the async ORM.",
                    "status": Post.Status.PUBLISHED,
                },
            )
            if made:
                Comment.objects.create(
                    post=post,
                    author_name="Reader",
                    email="reader@example.com",
                    body="Fast!",
                    is_approved=True,
                )

        self.stdout.write(self.style.SUCCESS("Seeded async blog demo data."))
