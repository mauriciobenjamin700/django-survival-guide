# Django Survival Guide 🐍

Welcome! This is a guide to learning **modern Django** from scratch — with
**clear typing**, **object orientation** and **zero magic**.

The idea is simple: instead of memorizing commands, you'll **understand what each
piece does and why**. Every page builds one concept on top of the previous one,
with complete, ready-to-run examples — in the style of the
[FastAPI documentation](https://fastapi.tiangolo.com).

## Where to start

<div class="grid cards" markdown>

-   🚀 __Get started__

    ---

    Set up the environment with `uv` and get the example blog running in minutes.

    [:octicons-arrow-right-24: Installation](get-started/installation.md)

-   📚 __Tutorial__

    ---

    Learn in order, one concept per page, building a blog from scratch up to a
    REST API.

    [:octicons-arrow-right-24: Start the tutorial](tutorial/project-setup.md)

-   🔎 __Reference__

    ---

    The dictionary: every class, option and `Meta`, with simple analogies and
    all the possibilities.

    [:octicons-arrow-right-24: See the map](referencia/index.md)

-   🧩 __API reference__

    ---

    The example code's documentation, generated automatically from its
    docstrings.

    [:octicons-arrow-right-24: Example API](referencia/api.md)

</div>

## What you'll build

A complete, working **blog**, evolving step by step:

1. **Pure Django** — models, admin, ORM, class-based views, templates, forms and
   authentication.
2. **REST API** — the same database exposed as an API with the
   Django REST Framework (DRF).

```text
Post ──< Comment          (a post has many comments)
Post >── Author           (each post has an author)
Post >──< Tag             (posts and tags: many-to-many)
```

All the code lives in the repository's [`example/`](https://github.com/mauriciobenjamin700/django-survival-guide/tree/main/example)
folder and **actually runs** — no loose snippets.

## Philosophy

!!! quote "Three principles"
    1. **Clear typing.** Every function, method and attribute is typed. Your
       editor helps you, and the reader understands the intent without guessing.
    2. **Object orientation.** We prefer class-based views and mixins: reusable
       behavior and composition instead of `if/else`.
    3. **Zero magic.** No "trust me, it works". Every Django convention is
       explained — what it does, when to use it, and what would happen without it.

!!! tip "Explanations for everyone"
    The **Reference** pages open each concept with a dead-simple analogy ("think
    like a child 🧒") and only then dive into the technical detail. The goal is
    to leave nobody behind.

## Versions used

| Tool | Version | Note |
| --- | --- | --- |
| Python | 3.14 | Guide target; the example runs on 3.13+ |
| Django | 6.0 | Latest stable series |
| Django REST Framework | 3.17 | API layer (advanced guide) |
| uv | 0.7+ | Dependency and Python manager |

Ready? Start with the **[Installation](get-started/installation.md)**. 🚀
