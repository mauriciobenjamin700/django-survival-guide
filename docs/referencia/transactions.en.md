# Reference: transactions

!!! quote "Think like a child 🧒"
    Imagine swapping trading cards: you give yours **and** get the other one. If
    only one half happens, someone gets robbed. A **transaction** is the "all or
    nothing" rule: either both things happen together, or neither does. If
    something goes wrong midway, the database pretends nothing happened (it does a
    *rollback*).

## Use case

Transferring balance between two accounts: take it from one **and** put it in the
other. If the second step fails, the first one can't count. `transaction.atomic`
guarantees that:

```python
from django.db import transaction


@transaction.atomic
def transfer(from_id: int, to_id: int, amount: int) -> None:
    """Move balance between accounts atomically (all-or-nothing)."""
    origem = Account.objects.select_for_update().get(pk=from_id)
    destino = Account.objects.select_for_update().get(pk=to_id)
    origem.balance -= amount
    destino.balance += amount
    origem.save()
    destino.save()
    # If any line above raises an error, NOTHING is written.
```

If `destino.save()` blows up, `origem.save()` is undone. No half-swap.

## Possibilities

### `atomic`: the two ways

| Way | When to use |
| --- | --- |
| Decorator `@transaction.atomic` | The whole function is one transaction |
| Context manager `with transaction.atomic():` | Only a section is transactional |

```python
# as a block
def view(request):
    do_stuff_outside_transaction()
    with transaction.atomic():
        a.save()
        b.save()          # a+b are atomic; the rest is not
```

!!! info "Outside `atomic`, each `save()` is already a transaction"
    Django runs in *autocommit*: each isolated operation is written right away.
    `atomic` is there to **group** several operations into a single "all or
    nothing".

### Nested transactions: savepoints

Think like a child: an `atomic` inside another one does not open a new
transaction — it creates a **return point** (savepoint) within the same one. If
the inner one fails, it rolls back only to that point; the outer one can keep
going.

```python
with transaction.atomic():          # outer transaction
    a.save()
    try:
        with transaction.atomic():  # savepoint
            b.save()
            raise ValueError()
    except ValueError:
        pass                         # undoes only b; a stays valid
    c.save()
```

### `select_for_update`: locking rows

Think like a child: hold the trading card in your hand so nobody swaps it at the
same time as you. It locks the rows until the transaction finishes.

```python
with transaction.atomic():
    conta = Account.objects.select_for_update().get(pk=1)
    conta.balance += 100
    conta.save()
```

!!! warning "`select_for_update` requires being inside `atomic`"
    The lock lasts until the end of the transaction. Outside an `atomic`, there is
    no transaction to hold the lock — Django raises an error. And it does **not**
    work on SQLite (use PostgreSQL/MySQL for real).

### `on_commit`: act only after the write went through

Think like a child: only set off the fireworks **after** the card swap really
counted — not midway, when a rollback could still happen.

```python
from django.db import transaction


def publish(post: Post) -> None:
    """Send a notification only after the DB commit succeeds."""
    with transaction.atomic():
        post.status = "published"
        post.save()
        transaction.on_commit(lambda: send_notification(post.id))   # (1)!
```

1. The email/notification only fires **if** the transaction is committed
    successfully. If there's a rollback, the callback doesn't run. It avoids "I
    emailed about a post that was never saved".

!!! danger "External side effects go in `on_commit`"
    Sending an email, dispatching a Celery task, calling an external API —
    **after** the commit. If you do that in the middle of the transaction and it
    reverts, the outside world was already affected but the database wasn't.
    `on_commit` fixes that.

### Manual control (rare, but it exists)

| Function | What it does |
| --- | --- |
| `transaction.set_autocommit(False)` | Turns off autocommit |
| `transaction.commit()` | Commits manually |
| `transaction.rollback()` | Rolls back manually |
| `transaction.get_connection().in_atomic_block` | Am I in a transaction? |

!!! tip "Prefer `atomic` over manual control"
    99% of cases are solved with `atomic` (decorator or block). Manual control is
    for very specific situations and is easy to get wrong.

### `ATOMIC_REQUESTS`: each request in a transaction

You can wrap **every** view in a transaction, per database:

```python
DATABASES = {
    "default": {
        # ...
        "ATOMIC_REQUESTS": True,
    }
}
```

With this, if the view raises an exception, everything it wrote is undone.
Simple, but it holds an open transaction for the entire request — weigh the cost.

!!! quote "📖 In the official docs"
    - [Database transactions](https://docs.djangoproject.com/en/stable/topics/db/transactions/)

## Recap

- Transaction = "all or nothing"; an error midway triggers a **rollback**.
- `atomic` as a decorator (whole function) or block (`with`, only a section);
  outside it, each `save()` already autocommits.
- Nested `atomic` becomes a **savepoint** (partial rollback).
- `select_for_update` locks rows (inside `atomic`, not on SQLite).
- External side effects (email, tasks) go in `transaction.on_commit`, so they
  only run if the commit goes through.
- `ATOMIC_REQUESTS=True` wraps each view in a transaction.

Transactions guarantee data consistency. Now for files: **[static and
media](static-media.md)**.
