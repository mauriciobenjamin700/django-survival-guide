# Installation

Let's set up the environment and get the example project running on your machine.

## Prerequisites

You need:

- **Python 3.13 or higher** (the guide targets 3.14).
- **[uv](https://docs.astral.sh/uv/)** — a fast, modern package and Python
  version manager. It's what we use instead of manual `pip` + `venv`.

!!! info "Why uv?"
    `uv` resolves dependencies, creates the virtual environment, and even downloads the
    right Python version — all with a single command and reproducibly (via
    `uv.lock`). No magic: a `pyproject.toml` file declares what the project
    needs, and `uv` handles the rest.

Install `uv` (Linux/macOS):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Cloning the project

```bash
git clone https://github.com/mauriciobenjamin700/django-survival-guide.git
cd django-survival-guide
```

## Installing the dependencies

A single command creates the virtual environment and installs everything in the
`pyproject.toml`:

```bash
uv sync
```

!!! check "What just happened"
    - `uv` read the `pyproject.toml`, downloaded the correct Python (if needed), and
      created the `.venv/` folder.
    - It installed Django, the Django REST Framework, and the documentation tools.
    - It locked the exact versions in `uv.lock`, so the environment is identical on
      any machine.

## Preparing the database and example data

The example uses **SQLite** — a single-file database with no server. Perfect
for learning. Enter the project folder and run the migrations:

```bash
cd example
uv run python manage.py migrate
```

Then, populate the blog with demo data:

```bash
uv run python manage.py seed_blog
```

!!! note "`uv run`"
    The `uv run` prefix runs the command **inside** the project's virtual
    environment, without you having to "activate" anything. It's equivalent to activating the `.venv` and
    running `python ...`, only explicit and forget-proof.

This command creates:

- a user **`demo`** with password **`demo12345`**;
- an author, a few tags, and published posts with comments.

## Running the server

```bash
uv run python manage.py runserver
```

Open **<http://127.0.0.1:8000/>** in your browser. You should see the list of posts. 🎉

| URL | What it is |
| --- | --- |
| `/` | List of published posts |
| `/posts/<slug>/` | Detail of a post + comments |
| `/login/` | Login (use `demo` / `demo12345`) |
| `/admin/` | Django admin panel |
| `/api/` | Browsable REST API (advanced guide) |

!!! tip "Accessing the admin"
    To get into `/admin/`, create a superuser:
    ```bash
    uv run python manage.py createsuperuser
    ```

## Running the documentation locally (optional)

This documentation is built with **MkDocs**. To view it locally:

```bash
uv run mkdocs serve
```

And open <http://127.0.0.1:8000/>. But normally you'd read the version published on
GitHub Pages — the link is at the top of the repository.

!!! quote "📖 In the official docs"
    - [Quick install guide](https://docs.djangoproject.com/en/stable/intro/install/)
    - [uv documentation](https://docs.astral.sh/uv/)

## Recap

- We use **uv** to manage Python and dependencies without manual steps.
- `uv sync` installs everything; `uv run <cmd>` runs inside the environment.
- `migrate` creates the tables; `seed_blog` populates example data.
- `runserver` brings the site up at `127.0.0.1:8000`.

With the project running, let's understand how it's put together — starting with the
**[project setup](../tutorial/project-setup.md)**.
