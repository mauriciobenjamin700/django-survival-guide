# How this project was built

A look behind the scenes: the decisions behind the guide and the example
project. If you want to build your own documentation in this style, here's the
map.

## The philosophy

Three principles guided every choice:

1. **Clear typing** — all the example code is typed, so the reader understands
   the intent without guessing.
2. **Object orientation** — class-based views and mixins, composition instead of
   `if/else`.
3. **Zero magic** — every Django convention is explained; no "trust me, it
   works".

And a fourth, about the writing: **explain it like to a child first**, with a
concrete analogy, and only then dive into the technical detail.

## The pieces

| Piece | Choice | Why |
| --- | --- | --- |
| Dependency management | [uv](https://docs.astral.sh/uv/) | Fast, reproducible (`uv.lock`), downloads Python itself |
| Framework | Django 6.0 | Latest stable series; the guide targets Python 3.14 |
| API | Django REST Framework | Mirrors the web concepts in the API layer |
| Docs | [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) | The de-facto standard for Python project docs |
| Bilingual | [mkdocs-static-i18n](https://ultrabug.github.io/mkdocs-static-i18n/) | PT-BR default + EN via `.en.md` suffix |
| Auto API | [mkdocstrings](https://mkdocstrings.github.io/) | The `example/` docstrings become the reference |
| Tests | pytest + pytest-django | Concise, with powerful fixtures |
| Deploy | Docker Compose + Gunicorn + WhiteNoise | Brings up app + Postgres with one command |

## The two-part structure

The repository separates **the guide** from **the code it teaches**:

```text
django-survival-guide/
├── docs/            # the guide (MkDocs, bilingual)
│   ├── tutorial/    # learn in order
│   └── referencia/  # look up by topic
├── example/         # the runnable Django blog
│   ├── config/
│   └── apps/blog/
├── Dockerfile
├── docker-compose.yml
└── mkdocs.yml
```

!!! info "Tutorial × Reference"
    The **Tutorial** is linear: it builds the blog from scratch, one concept per
    page. The **Reference** is a dictionary: each topic exhausted on one page, in
    the *use case → possibilities* format. One teaches the path; the other
    answers "and what does this option do?".

## The code always runs

No loose snippets. Every large example lives in `example/`, which:

- passes `python manage.py check`;
- has versioned migrations;
- has a green `pytest` suite;
- actually boots via `docker compose up`.

The [API reference](../referencia/api.md) page is generated **from the
docstrings** of that code — so the documentation never drifts from what runs.

## The bilingual flow

Every page is written first in **PT-BR** and then translated to **EN-US**,
keeping the code identical and translating only the prose (and example
comments/strings). The final build runs `mkdocs build --strict`: if something
doesn't resolve in both languages, it fails — the documentation never ships
broken.

## Recap

- Guide and code separated: `docs/` teaches, `example/` proves.
- Modern tooling: uv, Django 6, MkDocs Material + i18n + mkdocstrings.
- Philosophy: clear typing, OO, zero magic, and explaining like to a child.
- Everything runs and is verified (`check`, `pytest`, `--strict`, `docker
  compose`).
