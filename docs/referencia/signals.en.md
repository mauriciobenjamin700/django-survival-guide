# Reference: signals

!!! quote "Think like a child 🧒"
    A **signal** is a doorbell. When something happens in one part of the system
    (e.g. "a post was saved"), the bell rings. Anyone who cares arranges it
    beforehand: "when that bell rings, let me know so I can do such-and-such". That
    way one part of the code reacts to another **without** the two knowing each
    other directly.

## Use case

Every time a `User` is created, you want to automatically create their `Author`
profile. Instead of remembering to do that everywhere you create a user, you
"listen" for the signal that a user was saved:

```python
# apps/blog/signals.py
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.blog.models import Author

User = get_user_model()


@receiver(post_save, sender=User)
def create_author_profile(sender, instance, created, **kwargs) -> None:
    """Create an Author profile whenever a new user is created."""
    if created:
        Author.objects.create(user=instance, display_name=instance.username)
```

Now, whoever creates a user (admin, shell, API), the profile is born alongside it.

## Possibilities

### The signals you'll use most

| Signal | Rings when... |
| --- | --- |
| `pre_save` | Before saving an object |
| `post_save` | After saving (has `created: bool`) |
| `pre_delete` | Before deleting |
| `post_delete` | After deleting |
| `m2m_changed` | An M2M relation changes (add/remove/clear) |
| `pre_migrate` / `post_migrate` | Around migrations |
| `request_started` / `request_finished` | Start/end of a request |

### Anatomy of a receiver

Think like a child: the `@receiver` is the arrangement ("let me know when..."). The
function is what you do when the bell rings.

```python
@receiver(post_save, sender=Post)
def on_post_saved(sender, instance, created, **kwargs) -> None:
    """React to a Post being saved."""
    ...
```

| Parameter | What it is |
| --- | --- |
| `sender` | The **class** that sent the signal (`Post`) |
| `instance` | The **object** that was saved/deleted |
| `created` | `True` if it was a creation (only `post_save`) |
| `**kwargs` | Always include it — Django passes extras (`update_fields`, `raw`, etc.) |

!!! warning "`sender=` filters the doorbell"
    Without `sender=Post`, your receiver rings for **every** model saved in the
    project. Almost always you want to filter by a specific model.

### Wiring the receivers in `apps.py`

Receivers only work if the module gets **imported**. The right place is the
`ready()` method of the `AppConfig`:

```python
# apps/blog/apps.py
from django.apps import AppConfig


class BlogConfig(AppConfig):
    name = "apps.blog"
    label = "blog"

    def ready(self) -> None:
        """Import signal receivers so they get connected at startup."""
        from apps.blog import signals   # noqa: F401
```

!!! danger "Forgot `ready()`? The signal never rings"
    The #1 mistake with signals: writing the receiver and having it never run,
    because the `signals.py` module was never imported. Import it in `ready()`.

### Connecting without a decorator

An alternative to `@receiver`, handy for connecting dynamically:

```python
from django.db.models.signals import post_save

post_save.connect(create_author_profile, sender=User)
post_save.disconnect(create_author_profile, sender=User)   # disconnect
```

### Custom signals

You can create your own doorbell:

```python
import django.dispatch

post_published = django.dispatch.Signal()      # define

# fire it somewhere
post_published.send(sender=Post, post=my_post)

# listen
@receiver(post_published)
def notify(sender, post, **kwargs) -> None:
    ...
```

### When to **avoid** signals

!!! danger "Signals are powerful and treacherous"
    They hide the flow: looking at `user.save()`, you don't see that an `Author`
    was born. That makes code harder to read and debug. Prefer **explicit** code
    whenever you can:

    - Logic that belongs to the object → override `save()` on the model.
    - Multi-step orchestration → do it in a clear **service**/method.
    - Reacting to an event **from another app** you don't control → that's where
      signals shine.

    Rule: use a signal when you **can't** put the logic in the obvious place.

## Recap

- A signal is a doorbell: something happens, the arranged receivers react —
  decoupling the parts.
- `post_save`/`pre_save`/`post_delete`/`m2m_changed` are the most used;
  `@receiver(signal, sender=Model)` connects them.
- Parameters: `sender` (class), `instance` (object), `created` (only post_save),
  always `**kwargs`.
- Import the receivers in the `ready()` of the `AppConfig`, or they never ring.
- Prefer `save()`/services when the logic has an obvious home; use signals to
  react to events you don't control.

Signals react on the server. **[Sessions and messages](sessions-messages.md)**, on
the other hand, keep state between requests.
