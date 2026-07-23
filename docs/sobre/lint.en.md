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

```toml
# pyproject.toml
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

```toml
[tool.ruff.lint.per-file-ignores]
"**/tests/*" = ["S101", "ANN"]        # asserts and free typing in tests
"**/__init__.py" = ["F401"]           # re-exports aren't "unused imports"
"**/settings.py" = ["E501"]           # some config lines are long
```

## The ritual: `make fix`

One command fixes everything fixable (imports, quotes, whitespace, dead code) and
formats:

```bash
make fix        # = ruff check --fix .  &&  ruff format .
```

And the gates that **check without changing** (for CI and pre-commit):

| Command | Does |
| --- | --- |
| `make lint` | `ruff check .` — reports problems |
| `make format` | `ruff format .` — formats |
| `make fix` | autofix + format (the "repair") |
| `make type` | `mypy example` — checks types |
| `make check` | lint + type + test (all gates) |

## Types: mypy + django-stubs

Ruff **requires** annotations; [mypy](https://mypy.readthedocs.io/) **verifies**
they hold up. For mypy to understand Django (managers, fields, `settings`), we use
`django-stubs`.

```bash
uv add --group dev mypy django-stubs djangorestframework-stubs
```

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.13"
plugins = ["mypy_django_plugin.main", "mypy_drf_plugin.main"]
mypy_path = "example"
check_untyped_defs = true

[tool.django-stubs]
django_settings_module = "config.settings"
```

!!! warning "mypy with Django needs the plugin + stubs"
    Without `django-stubs` and the plugin, mypy complains about things that **are**
    correct in Django (e.g. `objects`, field types). The plugin teaches mypy to
    "read" Django. Migrations and tests are left out (`ignore_errors`).

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
- **Ruff** does lint + imports + formatting in one (fast); config with a broad
  `select` (including `ANN` for typing) and judicious `ignore`/`per-file-ignores`;
  **exclude migrations**.
- The ritual is `make fix` (repairs) and `make check` (lint + types + tests).
- **mypy + django-stubs** verify the types Ruff requires.
- Conventions: double quotes, type everything, docstrings, absolute imports, no
  inline comments.

!!! quote "📖 In the official docs"
    - [Ruff](https://docs.astral.sh/ruff/)
    - [mypy](https://mypy.readthedocs.io/)
    - [django-stubs](https://github.com/typeddjango/django-stubs)

See also how to contribute following these standards in
**[Contributing](contribuindo.md)**.
