# Contributing

Want to improve the guide — fix a typo, translate, add a page? Great! This
document shows how to run the project and which standards to follow.

## Set up the environment

```bash
git clone https://github.com/mauriciobenjamin700/django-survival-guide.git
cd django-survival-guide
uv sync --all-groups          # app + dev + docs + prod
```

## Running things

| Goal | Command |
| --- | --- |
| Blog server | `make run` (or `cd example && uv run python manage.py runserver`) |
| Tests | `make test` (or `uv run pytest`) |
| Docs locally | `make docs-serve` |
| Build docs (strict) | `make docs-build` |

!!! danger "The docs build must pass in `--strict`"
    Before opening a PR, run `make docs-build`. It runs `mkdocs build --strict`:
    **any** warning becomes an error. Broken link, page missing from `nav`, an
    unresolved reference — it all fails here.

## Documentation standards

This guide follows the [FastAPI documentation](https://fastapi.tiangolo.com) style:

- **One concept per page**, in learning order.
- **Complete, runnable examples** — no `...` in the middle of code that is
  supposed to work.
- **Admonitions** (`!!! tip`, `!!! warning`, `!!! danger`...) to layer
  information without breaking the flow.
- Every **Reference** page opens with a simple analogy ("think like a child 🧒"),
  then a **Use case**, then **Possibilities**, and ends with a **Recap**.

### Bilingual: PT-BR + EN-US

Every page exists in two languages via
[mkdocs-static-i18n](https://ultrabug.github.io/mkdocs-static-i18n/):

- `page.md` → Portuguese (default).
- `page.en.md` → English (same folder, `.en` suffix).

Internal links always point at the **PT name** (`page.md`) — i18n resolves the
right language on its own. Don't write `.en` in links.

### Adding a new page (checklist)

1. Create `docs/<section>/<page>.md` (PT) following the format above.
2. Create `docs/<section>/<page>.en.md` (EN).
3. Add it to `nav:` in `mkdocs.yml`.
4. Add the title translation under `nav_translations:` (the `en` block).
5. `make docs-build` — it must come out **clean**.

## Code standards (`example/`)

The example project is teaching material — the code is read by people learning.
So:

- **Type hints** everywhere (parameters, returns, attributes).
- **Google-style docstrings** in English on classes/methods.
- **Double quotes**, absolute imports.
- **Class-based views** by default.
- Run `make test` — the suite must pass.

## Commits

We use [Conventional Commits](https://www.conventionalcommits.org/):

```text
docs: add reference page on signals
feat(example): add tag filtering to the post list
fix(example): stamp published_at only once
test(example): cover comment moderation
```

Prefixes: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`.

## Recap

- `uv sync --all-groups`, then `make run` / `make test` / `make docs-serve`.
- Docs in the tiangolo style, bilingual (`.md` + `.en.md`), links without `.en`.
- `make docs-build` **strict** before every PR.
- Typed, CBV, tested code; conventional commits.
