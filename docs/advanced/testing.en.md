# Tests

Code without tests is code you're afraid to change. Django has great support
for testing, and here we use **pytest** with the **pytest-django** plugin — more concise
than the standard `unittest`, with powerful fixtures.

!!! quote "What to test in a Django project"
    - **Models** — business rules (is the `slug` generated? is `published_at`
      stamped?).
    - **Views** — do the pages respond? is access protected?
    - **API** — do the endpoints return what's expected? does the permission work?

## Installation

```bash
uv add --group dev pytest pytest-django
```

We configure pytest in `pyproject.toml`, pointing to the `settings` and where to find the
tests:

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
python_files = ["test_*.py", "tests.py"]
```

!!! info "Automatic test database"
    `pytest-django` creates a **temporary** database for the tests and destroys it at the
    end — your development database is never touched. Mark the tests that
    access the database with `@pytest.mark.django_db`.

## Testing a model

We check the `save()` rule: a published post gets `published_at`
automatically.

```python
import pytest

from apps.blog.models import Author, Post
from django.contrib.auth import get_user_model


@pytest.fixture
def author(db) -> Author:
    """Create a demo author backed by a user."""
    user = get_user_model().objects.create_user("ana", password="x")
    return Author.objects.create(user=user, display_name="Ana")


@pytest.mark.django_db
def test_publishing_stamps_published_at(author: Author) -> None:
    """Saving a post as PUBLISHED sets ``published_at`` and the slug."""
    post = Post.objects.create(
        title="Olá Mundo", body="...", author=author,
        status=Post.Status.PUBLISHED,
    )
    assert post.slug == "ola-mundo"
    assert post.published_at is not None
    assert post.is_published is True
```

- **`db` / `@pytest.mark.django_db`** — give access to the test database.
- **`@pytest.fixture`** — creates reusable data (the `author`) that tests
  request by parameter. It's the pytest way of doing setup.

## Testing the custom QuerySet

```python
@pytest.mark.django_db
def test_published_manager_excludes_drafts(author: Author) -> None:
    """The ``published()`` queryset returns only published posts."""
    Post.objects.create(title="Draft", body="x", author=author)
    Post.objects.create(
        title="Live", body="x", author=author, status=Post.Status.PUBLISHED,
    )
    assert Post.objects.published().count() == 1
```

## Testing a view

The **test client** simulates HTTP requests without bringing up a server:

```python
from django.test import Client


@pytest.mark.django_db
def test_post_list_returns_200(client: Client, author: Author) -> None:
    """The post list page renders successfully."""
    Post.objects.create(
        title="Live", body="x", author=author, status=Post.Status.PUBLISHED,
    )
    response = client.get("/")
    assert response.status_code == 200
    assert b"Live" in response.content


@pytest.mark.django_db
def test_create_view_requires_login(client: Client) -> None:
    """Anonymous users are redirected away from the create page."""
    response = client.get("/posts/new/")
    assert response.status_code == 302
    assert "/login/" in response["Location"]
```

- **`client`** — a pytest-django fixture, ready to use.
- The second test confirms the `LoginRequiredMixin`: an anonymous user gets a **302** to the
  login. Testing *security* is as important as testing the happy path.

## Testing the API

DRF brings an `APIClient` that speaks JSON:

```python
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_api_list_is_public(author: Author) -> None:
    """Anonymous clients can list published posts."""
    Post.objects.create(
        title="Live", body="x", author=author, status=Post.Status.PUBLISHED,
    )
    response = APIClient().get("/api/posts/")
    assert response.status_code == 200
    assert response.json()["count"] == 1


@pytest.mark.django_db
def test_api_create_requires_auth() -> None:
    """Anonymous clients cannot create posts."""
    response = APIClient().post("/api/posts/", {"title": "X", "body": "Y"})
    assert response.status_code in (401, 403)
```

## Running

```bash
uv run pytest             # todos os testes
uv run pytest -v          # verboso
uv run pytest -k list     # só os que casam com "list"
```

!!! tip "Test the behavior, not the implementation"
    Good tests check **what** the system does (the page opens, the draft doesn't
    show up, the anonymous user is blocked), not *how* it does it inside. That way you can
    refactor freely without rewriting the tests.

## Recap

- We use **pytest + pytest-django**; `DJANGO_SETTINGS_MODULE` in `pyproject.toml`.
- The test database is created and destroyed on its own; unlock it with `@pytest.mark.django_db`.
- **Fixtures** create reusable data.
- Test models (rules), views (status + protection), and the API (`APIClient`).
- Focus on observable behavior, not internal details.

🎉 You've reached the end of the guide! You have a complete Django project — typed, object-oriented, with web, API, and tests — and you understand **the why** behind each piece.
