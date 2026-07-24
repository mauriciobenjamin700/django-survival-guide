# Installation

On this page you'll **create your own Django project from scratch**, on your own
machine, from the very first command to Django's welcome screen in the browser.
No repository cloning: you type every step and understand what each one does.

!!! tip "Just want to see the finished example running?"
    There's an appendix at the end of the page: [Appendix — running the example
    blog](#appendix-running-the-example-blog). But we recommend doing the
    from-scratch path first — that's when it clicks.

## Prerequisites

You need:

- **Python 3.13 or higher** (the guide targets 3.14).
- **[uv](https://docs.astral.sh/uv/)** — a fast, modern package and Python
  version manager. It's what we use instead of manual `pip` + `venv`.

!!! info "Why uv?"
    `uv` resolves dependencies, creates the virtual environment, and even
    downloads the right Python version — all with a single command and
    reproducibly (via `uv.lock`). No magic: a `pyproject.toml` file declares what
    the project needs, and `uv` handles the rest.

Install `uv`:

=== "Linux / macOS"

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

=== "Windows (PowerShell)"

    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

Check that it worked:

```bash
uv --version
```

!!! note "You don't need to install Python first"
    If your machine doesn't have Python 3.13, `uv` downloads and uses the right
    version automatically in the next step. One problem less.

## Step 1 — create the project folder

```bash
uv init my-blog --python 3.13
cd my-blog
```

This creates the `my-blog/` folder with a Python project skeleton:

```text
my-blog/
├── .git/                 # git repository already initialized
├── .gitignore
├── .python-version       # pins the Python version (3.13)
├── README.md
├── main.py               # sample file — you can delete it
└── pyproject.toml        # where dependencies are declared
```

`main.py` is of no use here:

```bash
rm main.py
```

!!! info "What is `pyproject.toml`?"
    It's the project's "shopping list": name, required Python version, and the
    dependencies. Whoever clones your project later only needs `uv sync` to get
    exactly the same environment.

## Step 2 — install Django

```bash
uv add "django>=6.0,<7"
```

!!! check "What just happened"
    - `uv` created the `.venv/` folder (the project's virtual environment).
    - It downloaded Python 3.13, if you didn't have it yet.
    - It installed Django and its dependencies (`asgiref`, `sqlparse`).
    - It added `django>=6.0,<7` to `dependencies` in `pyproject.toml`.
    - It created `uv.lock` with the **exact** versions — that's what guarantees
      the environment will be identical on any machine.

!!! note "Why `>=6.0,<7`?"
    It accepts any fix and feature from the 6.x series (which are compatible
    with each other), but blocks Django 7, which may bring breaking changes. You
    decide when to take that jump instead of being surprised by it.

Check the installed version:

```bash
uv run django-admin --version
```

!!! note "`uv run`"
    The `uv run` prefix runs the command **inside** the project's virtual
    environment, without you having to "activate" anything. It's equivalent to
    activating the `.venv` and running `python ...`, only explicit and
    forget-proof.

## Step 3 — create the Django project

```bash
uv run django-admin startproject config .
```

!!! warning "Mind the trailing dot"
    The `.` at the end says "generate it here, in this folder". Without it,
    Django would create one more level (`my-blog/config/config/...`) — it works,
    but it's nested for no reason.

Now the folder has:

```text
my-blog/
├── manage.py             # entry point for every command
├── pyproject.toml
├── uv.lock
└── config/               # the "project": overall configuration
    ├── __init__.py
    ├── settings.py       # all the settings
    ├── urls.py           # root routing
    ├── asgi.py           # async entry point (production)
    └── wsgi.py           # sync entry point (production)
```

!!! info "`django-admin` vs `manage.py`"
    `django-admin` is the global command — used when the project **doesn't exist
    yet**. Once it does, you use `manage.py`, which is the same program, only it
    already knows which `settings.py` is yours.

## Step 4 — create the database

Django ships with its own tables (users, permissions, sessions, admin). They
don't exist until you run the migrations:

```bash
uv run python manage.py migrate
```

This creates the **`db.sqlite3`** file — a whole database in a single file, with
no server to install. Perfect for learning.

!!! note "Will I be stuck with SQLite?"
    No. Switching to PostgreSQL means changing the `DATABASES` dictionary in
    `settings.py` — the rest of the code stays the same. That's the ORM doing
    the translation work.

## Step 5 — start the server

```bash
uv run python manage.py runserver
```

Open **<http://127.0.0.1:8000/>**. You should see Django's welcome page, with a
rocket taking off: *"The install worked successfully! Congratulations!"* 🚀

!!! check "If the rocket showed up"
    Your Python, your virtual environment, Django, and the development server
    are all working. That's the foundation for everything that follows.

To stop the server: `Ctrl + C`.

!!! tip "Warning about unapplied migrations?"
    If the terminal complains about *"unapplied migration(s)"*, just run the
    `migrate` from step 4 again. `runserver` warns you, but doesn't apply them
    on its own.

## Step 6 — create your admin user

Django already ships a complete admin panel. To get into it, create a
superuser:

```bash
uv run python manage.py createsuperuser
```

It asks for a username, an email (optional), and a password. With the server
running, go to **<http://127.0.0.1:8000/admin/>** and log in.

!!! note "It's empty, and that's correct"
    For now the admin only shows **Users** and **Groups** — the tables Django
    itself brought along. Your models show up there once you create and register
    them, in the [Admin tutorial](../tutorial/admin.md).

## Your next steps

You have a working Django project, created by you. From here on, the tutorial
builds a **blog** on top of that foundation, one page per concept:

1. **[Setting up the project](../tutorial/project-setup.md)** — create the
   `blog` app, understand `settings.py`, and register the app.
2. **[Models and the ORM](../tutorial/models.md)** — the blog's tables.
3. …and so on, all the way to the REST API.

!!! tip "Do it, don't copy it"
    Type the commands and the code into *your* project instead of only reading.
    The reference code for each page lives in the
    [`example/`](https://github.com/mauriciobenjamin700/django-survival-guide/tree/main/example)
    folder of the repository, so you can compare when something doesn't match.

## Appendix — running the example blog

If you want to see the final result working (to compare, or to explore the
finished code), clone the guide's repository:

```bash
git clone https://github.com/mauriciobenjamin700/django-survival-guide.git
cd django-survival-guide
uv sync
```

`uv sync` reads `pyproject.toml` + `uv.lock` and reproduces the exact
environment: Django, Django REST Framework, and the documentation tools.

Prepare the database and populate it with demo data:

```bash
cd example
uv run python manage.py migrate
uv run python manage.py seed_blog
```

`seed_blog` creates:

- a user **`demo`** with password **`demo12345`**;
- an author, a few tags, and published posts with comments.

Start the server:

```bash
uv run python manage.py runserver
```

| URL | What it is |
| --- | --- |
| `/` | List of published posts |
| `/posts/<slug>/` | Detail of a post + comments |
| `/login/` | Login (use `demo` / `demo12345`) |
| `/admin/` | Django admin panel |
| `/api/` | Browsable REST API (advanced guide) |

??? info "Running this documentation locally"
    The documentation is built with **MkDocs**. Inside the cloned repository:

    ```bash
    uv run mkdocs serve
    ```

    And open <http://127.0.0.1:8000/>. Normally, though, you'd read the version
    published on GitHub Pages — the link is at the top of the repository.

!!! quote "📖 In the official docs"
    - [Quick install guide](https://docs.djangoproject.com/en/stable/intro/install/)
    - [Writing your first Django app](https://docs.djangoproject.com/en/stable/intro/tutorial01/)
    - [uv documentation](https://docs.astral.sh/uv/)

## Recap

- **uv** manages Python, the virtual environment, and dependencies: `uv init`
  creates the project, `uv add` installs, `uv run <cmd>` runs inside the
  environment.
- `django-admin startproject config .` generates the project (`config/` +
  `manage.py`).
- `migrate` creates the initial tables in `db.sqlite3`.
- `runserver` brings the site up at `127.0.0.1:8000` — rocket on screen = all
  good.
- `createsuperuser` gives you access to `/admin/`.

With the skeleton standing, let's understand how it's organized — and create the
blog app — in **[Setting up the project](../tutorial/project-setup.md)**.
