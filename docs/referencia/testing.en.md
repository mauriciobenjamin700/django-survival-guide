# Reference: testing in depth

!!! quote "Think like a child 🧒"
    Tests are your code's **seatbelt**. You change something, press a button
    (`pytest`), and it tells you right away if something broke. Without them, every
    change is a leap in the dark. With them, you refactor fearlessly.

## Use case

You want to make sure a published post gets `published_at`, that the page opens,
and that the API blocks anyone who isn't logged in. Three tests, with `pytest`:

```python
import pytest
from apps.blog.models import Post


@pytest.mark.django_db
def test_publishing_stamps_date(author) -> None:
    """Publishing a post stamps published_at."""
    post = Post.objects.create(
        title="Olá", body="x", author=author, status=Post.Status.PUBLISHED
    )
    assert post.published_at is not None
```

## Possibilities

### pytest-django × unittest

| | `pytest` + pytest-django | `unittest` (Django `TestCase`) |
| --- | --- | --- |
| Style | Functions + fixtures | Classes + `setUp` methods |
| Database | `@pytest.mark.django_db` | Automatic in `TestCase` |
| Verbosity | Lower | Higher |

In this guide we use **pytest**: leaner and with powerful fixtures.

### Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
pythonpath = ["example"]
python_files = ["test_*.py", "tests.py"]
```

### Database access: `django_db`

!!! danger "Without the mark, the test doesn't touch the database"
    For safety, pytest-django **blocks** the database by default. Mark the tests
    that need it with `@pytest.mark.django_db` (or request the `db` fixture).
    Forgot? The error is `Database access not allowed`.

The test database is created and destroyed on its own — your real `db.sqlite3` is
never touched.

### Fixtures: reusable data

Think like a child: a fixture is a "toy that's already assembled" that any test
can ask for just by naming it in the parameter.

```python
# conftest.py — visible to all the tests around it
import pytest
from django.contrib.auth import get_user_model
from apps.blog.models import Author


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user("ana", password="x")


@pytest.fixture
def author(user):
    return Author.objects.create(user=user, display_name="Ana")
```

| Resource | Role |
| --- | --- |
| `conftest.py` | Shared fixtures (no import needed) |
| `@pytest.fixture` | Defines a reusable piece of data/resource |
| Fixtures request fixtures | `author` receives `user` — they compose |
| `scope="session"` | Created once for the whole test session |

### Test clients

=== "Views (HTML) — `client`"

    ```python
    def test_home(client, published_post):
        response = client.get("/")
        assert response.status_code == 200

    def test_login_required(client):
        response = client.get("/posts/new/")
        assert response.status_code == 302

    def test_authed(client, user):
        client.force_login(user)         # shortcut: log in without a password
        assert client.get("/posts/new/").status_code == 200
    ```

=== "API (JSON) — `APIClient`"

    ```python
    from rest_framework.test import APIClient

    def test_api_public(published_post):
        r = APIClient().get("/api/posts/")
        assert r.status_code == 200
        assert r.json()["count"] == 1

    def test_api_auth(user):
        c = APIClient()
        c.force_authenticate(user=user)
        r = c.post("/api/posts/", {"title": "X", "body": "Y"}, format="json")
        assert r.status_code == 201
    ```

| Client | For |
| --- | --- |
| `client` (fixture) | HTML views |
| `APIClient` (DRF) | JSON endpoints |
| `.force_login(user)` | Log in without going through the screen |
| `.force_authenticate(user=...)` | Authenticate on the API |

### Counting queries: `django_assert_num_queries`

Think like a child: it counts how many times the test "opened the database box" —
it catches N+1 red-handed.

```python
def test_list_is_efficient(client, django_assert_num_queries, published_post):
    """The list page must not explode into N+1 queries."""
    with django_assert_num_queries(3):
        client.get("/")
```

### Mocking: faking the outside world

Don't test real email/HTTP — fake it:

```python
from unittest.mock import patch


@patch("apps.blog.services.send_notification")
def test_publish_notifies(mock_send, author):
    """Publishing triggers a notification (mocked)."""
    Post.objects.create(title="X", body="y", author=author,
                        status=Post.Status.PUBLISHED)
    # ... trigger the logic ...
    mock_send.assert_called_once()
```

!!! tip "Mock where it's USED, not where it's defined"
    Use `@patch("apps.blog.services.send_notification")` (the path where the code
    **imports/uses** it), not `@patch("email_lib.send")`. Getting the path wrong is
    the #1 reason for "my mock didn't take".

### Parametrize: one test, many cases

```python
import pytest


@pytest.mark.parametrize("status,expected", [
    ("published", 200),
    ("draft", 404),
])
@pytest.mark.django_db
def test_visibility(client, author, status, expected):
    post = Post.objects.create(title="X", body="y", author=author, status=status)
    assert client.get(f"/posts/{post.slug}/").status_code == expected
```

### Run and measure coverage

```bash
uv run pytest                       # everything
uv run pytest -v                    # verbose
uv run pytest -k api                # only those matching "api"
uv run pytest -x                    # stop at the first error
uv run pytest --cov=apps            # coverage (needs pytest-cov)
```

!!! tip "Test behavior, not implementation"
    Good tests check **what** happens (the page opens, the draft disappears, the
    anonymous user is blocked), not *how* on the inside. That way you refactor
    freely without rewriting the tests.

!!! quote "📖 In the official docs"
    - [Testing in Django](https://docs.djangoproject.com/en/stable/topics/testing/)
    - [pytest-django](https://pytest-django.readthedocs.io/)

## Recap

- pytest + pytest-django; unlock the database with `@pytest.mark.django_db` (the
  test database is isolated and disposable).
- **Fixtures** in `conftest.py` build reusable data and compose with each other.
- `client` (HTML) and `APIClient` (JSON); `force_login`/`force_authenticate`.
- `django_assert_num_queries` catches N+1; `@patch` fakes the outside world (patch
  at the **usage** path); `parametrize` runs many cases.
- Focus on observable behavior; measure it with `--cov`.

Closing the views loop: **[generic views & mixins](generic-views.md)**.
