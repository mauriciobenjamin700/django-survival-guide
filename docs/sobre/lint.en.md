# Linting & best practices

Learning code is read by lots of people — so it has to be **consistent** and
**readable**. Instead of arguing about style in every review, we let a tool handle
it automatically. This page shows the setup this project uses and recommends.

!!! quote "Think like a child 🧒"
    The **linter** is the teacher who grades your essay: it flags the missing
    comma, the repeated word, the crooked sentence — and even fixes what it can.
    You stop losing time on details and focus on the idea. And since it's always
    the same teacher, everyone writes the same way.

## One tool for everything: Ruff

[Ruff](https://docs.astral.sh/ruff/) does, very fast, what used to take several
tools (flake8 + isort + black + pyupgrade): **linting**, **import sorting** and
**formatting** — in a single binary.

```bash
uv add --group dev ruff
```

That command installs Ruff and records it in the `dev` group of your
`pyproject.toml`. Installed, it still doesn't know **which** rules you want —
that comes from the configuration.

### Where the configuration goes

Open the `pyproject.toml` at the **project root** (same folder as the `Makefile`,
one level above `example/`) and **paste the blocks below at the end of the file**:

```toml
# pyproject.toml  ← paste this at the end of the file
[tool.ruff]
line-length = 88
target-version = "py313"
extend-exclude = ["**/migrations/*"]      # (1)!

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "N", "SIM", "RUF", "ANN"]
ignore = ["ANN401", "ANN002", "ANN003", "RUF012"]

[tool.ruff.format]
quote-style = "double"                     # (2)!
indent-style = "space"
```

1. **Migrations are generated** by Django — no point linting them. Always exclude.
2. Double quotes everywhere, no debate.

!!! info "`pyproject.toml` is the project's control panel"
    Each `[some.thing]` block is a **section** of that panel: `[tool.ruff]`
    configures Ruff, `[tool.mypy]` configures mypy, `[project]` describes your
    package. Section order doesn't matter — but **don't repeat** a section that
    already exists: if the file already has a `[tool.ruff]`, edit that one instead
    of pasting a second.

### What each rule group catches

| Code | Rules |
| --- | --- |
| `E`/`W` | PEP 8 style (spacing, lines) |
| `F` | Real errors (unused variable, missing import) |
| `I` | Import sorting (stdlib → third-party → local) |
| `B` | Likely bugs (flake8-bugbear) |
| `C4` | Cleaner comprehensions |
| `UP` | Modernize syntax (pyupgrade) |
| `N` | Naming (PascalCase for classes, snake_case for functions) |
| `SIM` | Simplifications (redundant `if`, etc.) |
| `ANN` | Requires **type annotations** |
| `RUF` | Ruff's own rules |

!!! tip "Why turn on `ANN` (typing)"
    `ANN` forces you to annotate functions and methods. That's our *clear typing*
    principle becoming an automatic rule — your editor helps you and the reader
    grasps the intent. We only ignore `ANN401` (allow explicit `Any`) and the
    `*args`/`**kwargs` annotations, which are just noise.

### Per-file ignores (with judgment)

Still in `pyproject.toml`, right below the `[tool.ruff.lint]` block you pasted:

```toml
# pyproject.toml
[tool.ruff.lint.per-file-ignores]
"**/tests/*" = ["S101", "ANN"]        # asserts and free typing in tests
"**/__init__.py" = ["F401"]           # re-exports aren't "unused imports"
"**/settings.py" = ["E501"]           # some config lines are long
```

## Before the ritual: the `Makefile`

From here on you'll see commands like `make fix` and `make check`. They **don't
come** from Python, `uv` or Ruff — they come from a file called `Makefile` that
**you write yourself** at the project root. It's just a list of named shortcuts:
`make fix` means "run whatever is written in the `fix` recipe".

!!! quote "Think like a child 🧒"
    The `Makefile` is the **note stuck on the fridge door**. Instead of recalling
    the whole recipe every time ("mix, beat, bake 40 min"), you write it once and
    give it a name: *cake*. Then you just shout the name. `make fix` is shouting
    the recipe's name — the computer remembers the steps.

### 1. Create the file

At the **project root** (same folder as `pyproject.toml`), create a file named
exactly `Makefile` — capital `M`, **no extension** (not `Makefile.txt`):

```text
my-project/
├── Makefile          # ← create this file
├── pyproject.toml
├── manage.py
├── config/           # settings.py, urls.py, wsgi.py
└── apps/
    └── blog/
```

`make` looks for the `Makefile` in the folder you're standing in — that's why
`make ...` commands only work from the **project root** (the folder with
`manage.py`).

### 2. Paste this content

```make
.PHONY: help lint format fix type test check

help:  ## List the available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

lint:  ## Check lint (ruff), without changing anything
	uv run ruff check .

format:  ## Format the code (ruff format)
	uv run ruff format .

fix:  ## Apply every ruff autofix + format
	uv run ruff check --fix .
	uv run ruff format .

type:  ## Type checking (mypy + django-stubs)
	uv run mypy apps config

test:  ## Run the test suite
	uv run pytest -q

check: lint type test  ## Run all gates (lint + types + tests)
```

Reading that out loud: each `name:` is a **recipe** (called a *target*), and the
indented lines under it are the commands it runs. `check: lint type test` has no
commands of its own — it just says "run those three recipes, in that order". The
`## text` after the colon is the description `make help` prints.

!!! warning "Adjust the paths for **your** project"
    Ruff (`lint`, `format`, `fix`) gets `.` — the current folder — so it works in
    any project unchanged. **mypy is different**: you tell it which folders to
    check. Above it's `apps config`, the layout this guide teaches:

    | What you have | What to pass to mypy |
    | --- | --- |
    | `apps/` + `config/` at the root (this guide) | `uv run mypy apps config` |
    | everything at the root, no `apps/` | `uv run mypy .` |
    | a single app, e.g. `blog/` + `config/` | `uv run mypy blog config` |
    | project inside a subfolder, e.g. `src/` | `uv run mypy src` |

    Passing `.` works too and also covers `manage.py` — mypy skips `.venv` on its
    own. Migrations are left out by `exclude` (next section). If the command
    complains about a module it can't find, the problem is `mypy_path`, not the
    folder list.

!!! note "This repository uses different paths"
    The guide keeps its example project inside `example/`, so the
    [repo's `Makefile`](https://github.com/mauriciobenjamin700/django-survival-guide/blob/main/Makefile)
    checks both projects in **separate calls**, and the Django commands run with
    `cd example`:

    ```make
    type:
    	uv run mypy example
    	uv run mypy example_async
    ```

    Separate because both have an `apps` package, and `mypy example example_async`
    in one go dies with `Duplicate module named "apps"`. In **your** project
    `manage.py` sits at the root — don't copy the `example/` wrapper.

!!! danger "`Makefile` indentation is TAB, not spaces"
    This is the classic trap: command lines **must** start with a real **TAB**
    character. If your editor converts TAB into spaces, `make` fails with:

    ```text
    Makefile:5: *** missing separator.  Stop.
    ```

    In VS Code, open the `Makefile` and click **Spaces: 4** in the bottom bar →
    **Indent Using Tabs**. Copying the block above from here already brings the
    TAB along — but double-check if you hit the error.

### 3. Try it

```bash
make help
```

It should list the commands with their descriptions. From then on the shortcuts
work:

```bash
make fix        # = ruff check --fix .  &&  ruff format .
```

!!! tip "The `Makefile` grows with the project"
    This is the minimum for lint and types. This guide's own `Makefile` also has
    `make install`, `make run`, `make migrate`, `make seed`, `make docs-serve` —
    look at the [`Makefile` at the repository
    root](https://github.com/mauriciobenjamin700/django-survival-guide/blob/main/Makefile)
    to copy the full set. The rule: **any command you type twice deserves a
    recipe**.

## The ritual: `make fix`

One command fixes everything fixable (imports, quotes, whitespace, dead code) and
formats:

```bash
make fix
```

And the gates that **check without changing** (for CI and pre-commit):

| Command | Does |
| --- | --- |
| `make lint` | `ruff check .` — reports problems |
| `make format` | `ruff format .` — formats |
| `make fix` | autofix + format (the "repair") |
| `make type` | `mypy apps config` — checks types |
| `make check` | lint + type + test (all gates) |

### I don't have `make` (or I'm on Windows)

`make` ships with macOS (via the *Command Line Tools*) and most Linux distros. If
`make help` answers `command not found`:

=== "Linux (Debian/Ubuntu)"

    ```bash
    sudo apt install make
    ```

=== "macOS"

    ```bash
    xcode-select --install
    ```

=== "Windows"

    Use **WSL** (recommended — it's this guide's environment) or install via
    [Chocolatey](https://chocolatey.org/):

    ```powershell
    choco install make
    ```

And if you'd rather install nothing, **no command here depends on `make`** — it
only shortens them. The direct equivalents:

| Shortcut | Real command |
| --- | --- |
| `make lint` | `uv run ruff check .` |
| `make format` | `uv run ruff format .` |
| `make fix` | `uv run ruff check --fix . && uv run ruff format .` |
| `make type` | `uv run mypy apps config` |
| `make test` | `uv run pytest -q` |
| `make check` | the three above, in sequence |

## Types: mypy + django-stubs

Ruff **requires** annotations; [mypy](https://mypy.readthedocs.io/) **verifies**
they hold up. For mypy to understand Django (managers, fields, `settings`), we use
`django-stubs`.

```bash
uv add --group dev mypy django-stubs djangorestframework-stubs
```

And, again, at the end of `pyproject.toml`:

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.13"
plugins = ["mypy_django_plugin.main", "mypy_drf_plugin.main"]
mypy_path = "."                                   # (1)!
check_untyped_defs = true
exclude = ['migrations/']

[tool.django-stubs]
django_settings_module = "config.settings"        # (2)!
```

1. **Where mypy looks for your modules.** Use the folder that contains
   `manage.py` — in this guide's layout, the root itself (`"."`). If your project
   lives in a subfolder (`src/`, `backend/`, or this repo's `example/`), point at
   it: `mypy_path = "src"`. Getting this wrong gives you `Cannot find
   implementation or library stub for module named "apps.blog"`.
2. **Your settings' import path** — exactly what's in
   `manage.py`/`DJANGO_SETTINGS_MODULE`. With `config/settings.py` it's
   `"config.settings"`; if you split by environment (`config/settings/dev.py`),
   it's `"config.settings.dev"`. The plugin **imports** that module to read your
   models — wrong settings means mypy won't run at all.

!!! warning "mypy with Django needs the plugin + stubs"
    Without `django-stubs` and the plugin, mypy complains about things that **are**
    correct in Django (e.g. `objects`, field types). The plugin teaches mypy to
    "read" Django. Migrations are left out via `exclude` — they're generated, no
    point checking them.

!!! tip "Check before moving on"
    ```bash
    make type        # or: uv run mypy apps config
    ```

    Type errors in your own code are expected — that's the point. What should
    **not** show up is `Cannot find implementation`, `django_settings_module is not
    set` or `ImproperlyConfigured` — those three mean the two settings above are
    wrong, not your code.

## The conventions the linter enforces

Beyond the automatic rules, we follow conventions that let the code breathe:

- **Double quotes** always (`"text"`).
- **Type everything**: parameters, returns, attributes.
- **Google-style docstrings** on classes/methods (in English, in our case).
- **Absolute imports**, grouped (Ruff's `I` sorts them).
- **No inline comment** explaining the *why* — that goes in the **docstring**. The
  code says *what*; the docstring says *why*.

!!! tip "Run it before every commit"
    The habit: `make fix` (repairs) → `make check` (ensures). To automate, set up
    a **pre-commit** hook that runs `ruff check --fix` and `ruff format` on each
    commit — so nobody forgets.

## Recap

- A linter keeps code consistent and readable without manual bikeshedding.
- **Ruff** does lint + imports + formatting in one (fast); the config goes into
  `[tool.ruff...]` blocks pasted at the end of **`pyproject.toml`**, with a broad
  `select` (including `ANN` for typing) and judicious `ignore`/`per-file-ignores`;
  **exclude migrations**.
- The `make ...` commands come from a **`Makefile`** you create at the root — named
  shortcuts, indented with **TAB**. Without `make`, run the `uv run ...` commands
  directly.
- The ritual is `make fix` (repairs) and `make check` (lint + types + tests).
- **mypy + django-stubs** verify the types Ruff requires — and here the paths are
  **yours**: which folders to check (`mypy apps config`), `mypy_path` pointing at
  the folder holding `manage.py`, and `django_settings_module` set to your
  settings' import path.
- Conventions: double quotes, type everything, docstrings, absolute imports, no
  inline comments.

!!! quote "📖 In the official docs"
    - [Ruff](https://docs.astral.sh/ruff/)
    - [mypy](https://mypy.readthedocs.io/)
    - [django-stubs](https://github.com/typeddjango/django-stubs)

See also how to contribute following these standards in
**[Contributing](contribuindo.md)**.
