# Reference

!!! quote "Think like a child 🧒"
    The **Tutorial** is the class: you learn in order, one step at a time. This
    **Reference** is the dictionary: you come here when you already know what
    you're looking for and want the detail — "what options does this field have?",
    "how does the cache work?". Each page opens with a simple analogy, shows a
    **use case**, and then exhausts the **possibilities**.

!!! tip "How each page is organized"
    - **Think like a child** — the idea in an everyday analogy.
    - **Use case** — a minimal, concrete example, ready to run.
    - **Possibilities** — all the options/parameters, in tables + examples.
    - **Recap** — the summary to make it stick.

## Topic map

### 🗃️ Models and database

| Page | What it covers |
| --- | --- |
| [Models — fields](models-fields.md) | Every field type and its options |
| [Models — Meta](models-meta.md) | Table configuration (ordering, constraints, abstract...) |
| [Custom fields](custom-fields.md) | Build your own field type |
| [Content types & generic relations](contenttypes.md) | Point at any model |
| [QuerySet API](querysets-api.md) | Fetching data: filters, lookups, `F`/`Q`, N+1 |
| [Advanced ORM (expressions)](orm-expressions.md) | `Case`/`When`, `Subquery`, functions, window |
| [Aggregation & group by](aggregation-groupby.md) | `aggregate`/`annotate`, per-group counts |
| [Transactions](transactions.md) | `atomic`, savepoints, `select_for_update`, `on_commit` |

### 🌐 Web layer (HTTP)

| Page | What it covers |
| --- | --- |
| [Class-based views](views-cbv.md) | Attributes, hooks, execution order |
| [Generic views & mixins](generic-views.md) | `TemplateView`/`RedirectView`/`FormView`, mixin catalog |
| [URLs & converters](urls.md) | `path`, converters, namespaces, `reverse` |
| [Templates](templates.md) | Tags, filters, inheritance, custom tags |
| [Forms & ModelForm](forms.md) | Validation, widgets, `clean` |
| [Validators & validation](validators.md) | Validators, `clean`, `full_clean` |
| [Formsets](formsets.md) | Several forms at once |

### 🔐 Users, session and state

| Page | What it covers |
| --- | --- |
| [Authentication & permissions](auth.md) | `User`, mixins, groups, custom user |
| [Sessions & messages](sessions-messages.md) | State between requests, flash messages |
| [Cache](cache.md) | Backends, `cache_page`, invalidation |

### ⚙️ Infrastructure and operations

| Page | What it covers |
| --- | --- |
| [Settings](settings.md) | Configuration, security, environments |
| [Middleware](middleware.md) | Layers around requests |
| [Signals](signals.md) | Reacting to model events |
| [Management commands](management-commands.md) | Your own `manage.py <cmd>` |
| [Static files & media](static-media.md) | CSS/JS × uploads |
| [Storages](storages.md) | Where files live (disk, S3) |
| [i18n & translations](i18n.md) | A site in several languages |
| [Deployment](deploy.md) | Going live safely |
| [Deploy with Docker Compose](deploy-docker.md) | Containers: app + Postgres |

### 🧪 Quality and API

| Page | What it covers |
| --- | --- |
| [Testing in depth](testing.md) | pytest, fixtures, clients, mocking |
| [DRF — serializers & viewsets](drf.md) | REST API over the same models |
| [API reference (code)](api.md) | Auto docs from the example's docstrings |

!!! info "New to Django?"
    Start with the [Tutorial](../tutorial/project-setup.md), which builds the
    example blog from scratch. Come back here when you want to dig deeper into a
    specific topic.
