# Django Survival Guide 🐍

Welcome! This is a guide to learning **modern Django** from scratch — with
**clear typing**, **object orientation**, and **zero magic**.

The idea is simple: instead of memorizing commands, you'll **understand what each
piece does and why**. Every page builds one concept on top of the previous one, with
complete, ready-to-run examples — in the style of the
[FastAPI documentation](https://fastapi.tiangolo.com).

!!! info "Who this guide is for"
    - Those who know **Python** (functions, classes, type hints) and want to learn Django.
    - Those who have used Django "by guesswork" and want to understand what happens under the hood.
    - Those who prefer **class-based views** and explicit, typed code.

## What you'll build

A complete, working **blog**, growing progressively:

1. **Pure Django** — models, admin, ORM, class-based views, templates,
   forms, and authentication.
2. **REST API** — the same database exposed as an API with the
   Django REST Framework (DRF).

```text
Post ──< Comment          (um post tem vários comentários)
Post >── Author           (cada post tem um autor)
Post >──< Tag             (posts e tags: muitos-para-muitos)
```

All the code lives in the [`example/`](https://github.com/mauriciobenjamin700/django-survival-guide/tree/main/example)
folder of the repository and **actually runs** — no loose snippets.

## Philosophy

!!! quote "Three principles"
    1. **Clear typing.** Every function, method, and attribute is typed. The editor
       helps you, and the reader understands the intent without guessing.
    2. **Object orientation.** We prefer class-based views and mixins:
       reusable behavior and composition instead of `if/else`.
    3. **Zero magic.** No "trust it and it works." Every Django convention is
       explained — what it does, when to use it, and what would happen without it.

## Versions used

| Tool | Version | Note |
| --- | --- | --- |
| Python | 3.14 | Guide's target; the example runs on 3.13+ |
| Django | 6.0 | Latest stable series |
| Django REST Framework | 3.17 | API layer (advanced guide) |
| uv | 0.7+ | Dependency and Python manager |

!!! tip "How to get the most out of it"
    Read in the order of the menu on the left. Each page ends with a short
    **Recap**. Run the code as you go — learning Django is learning by doing. 🚀

Ready? Start with **[Installation](get-started/installation.md)**.
