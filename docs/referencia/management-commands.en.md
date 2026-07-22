# Reference: management commands

!!! quote "Think like a child 🧒"
    You already use ready-made commands: `migrate`, `runserver`, `createsuperuser`.
    A **management command** is one of those buttons that **you** create. It's a
    little program that runs from the terminal, already with access to your whole
    project (database, models, settings) — perfect for tasks outside the site:
    importing data, cleaning up junk, sending a report.

## Use case

You want to seed the blog with test data by running `python manage.py seed_blog`.
Creating a command means writing a `Command` class with a `handle` method:

```python
# apps/blog/management/commands/seed_blog.py
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.blog.models import Post


class Command(BaseCommand):
    """Seed the blog with demo data."""

    help = "Seed the blog with demo data."

    @transaction.atomic
    def handle(self, *args: object, **options: object) -> None:
        """Run the command."""
        Post.objects.get_or_create(title="Hello World", defaults={"body": "..."})
        self.stdout.write(self.style.SUCCESS("Data created!"))
```

Where the file lives **matters**: `app/management/commands/<name>.py`. The file
name becomes the command name.

## Possibilities

### The folder structure (required)

```text
apps/blog/
└── management/
    ├── __init__.py                 # must exist
    └── commands/
        ├── __init__.py             # must exist
        └── seed_blog.py            # -> python manage.py seed_blog
```

!!! danger "Missing an `__init__.py`? The command won't show up"
    Django only discovers commands in `management/commands/` **if** both folders
    have an `__init__.py` and the app is in `INSTALLED_APPS`. A "command not found"
    error is almost always this.

### Class attributes and methods

| Member | Role |
| --- | --- |
| `help` | Text shown in `manage.py <cmd> --help` |
| `handle(self, *args, **options)` | The command body (required) |
| `add_arguments(self, parser)` | Declares arguments/options |
| `self.stdout` / `self.stderr` | Output (use these instead of `print`) |
| `self.style` | Colors: `SUCCESS`, `WARNING`, `ERROR`, `NOTICE` |

### Receiving arguments

Think like a child: `add_arguments` is where you say which "LEGO pieces" the
command accepts; they arrive in `options` inside `handle`.

```python
class Command(BaseCommand):
    help = "Delete draft posts older than N days."

    def add_arguments(self, parser) -> None:
        """Declare command-line arguments."""
        parser.add_argument("days", type=int, help="Minimum age in days")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only show, don't delete",
        )

    def handle(self, *args: object, **options: object) -> None:
        """Delete (or preview) old draft posts."""
        days: int = options["days"]
        dry_run: bool = options["dry_run"]
        qs = Post.objects.filter(status="draft").older_than(days)

        if dry_run:
            self.stdout.write(self.style.NOTICE(f"{qs.count()} would be deleted."))
            return

        deleted, _ = qs.delete()
        self.stdout.write(self.style.SUCCESS(f"{deleted} deleted."))
```

Usage:

```bash
python manage.py cleanup_drafts 30 --dry-run
python manage.py cleanup_drafts 30
```

| `add_argument` | Argument type |
| --- | --- |
| `parser.add_argument("name")` | Required positional |
| `parser.add_argument("--flag", action="store_true")` | Boolean option |
| `parser.add_argument("--n", type=int, default=10)` | Option with a value |
| `parser.add_argument("ids", nargs="+", type=int)` | Multiple values |

### Best practices

!!! tip "Use `self.stdout.write`, not `print`"
    `self.stdout.write(...)` respects redirection, tests, and `--verbosity`.
    `print` bypasses all of that. For colors, wrap with `self.style.SUCCESS(...)`.

!!! tip "Wrap database writes in `@transaction.atomic`"
    If the command makes many changes and something fails halfway, the transaction
    guarantees "all or nothing" — without leaving the database half-done.

### Testing a command

```python
from io import StringIO
from django.core.management import call_command


def test_seed_creates_posts(db) -> None:
    out = StringIO()
    call_command("seed_blog", stdout=out)
    assert "Data created" in out.getvalue()
    assert Post.objects.exists()
```

### Built-in commands worth knowing

| Command | What for |
| --- | --- |
| `shell` / `shell_plus` | Python console with the project loaded |
| `dbshell` | Database console |
| `dumpdata` / `loaddata` | Export/import data (fixtures) |
| `collectstatic` | Gathers static files (deploy) |
| `createsuperuser` | Creates an admin |
| `check` | Validates the project |
| `showmigrations` | Lists migrations |

## Recap

- A management command = a `manage.py <cmd>` that you create; it runs with the
  whole project loaded.
- File at `app/management/commands/<name>.py`; **both** `__init__.py` files must
  exist.
- The `Command` class: `help`, `handle()`, `add_arguments(parser)`; output via
  `self.stdout.write` + `self.style.*` (never `print`).
- Arguments via `parser.add_argument` (positionals, `--flags`, `nargs`).
- Wrap writes in `@transaction.atomic`; test with `call_command`.

With everything ready, only one thing is left: getting it live — the
**[deploy](deploy.md)**.
