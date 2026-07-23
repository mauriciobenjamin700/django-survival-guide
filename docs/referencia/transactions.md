# Referência: transações

!!! quote "Pensa como criança 🧒"
    Imagine trocar figurinhas: você dá a sua **e** recebe a outra. Se só uma
    metade acontecer, alguém sai roubado. Uma **transação** é a regra "tudo ou
    nada": ou as duas coisas acontecem juntas, ou nenhuma. Se der problema no
    meio, o banco finge que nada aconteceu (faz *rollback*).

## Caso de uso

Transferir saldo entre duas contas: tirar de uma **e** pôr na outra. Se o
segundo passo falhar, o primeiro não pode valer. `transaction.atomic` garante
isso:

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
    # Se qualquer linha acima levantar erro, NADA é gravado.
```

Se o `destino.save()` explodir, o `origem.save()` é desfeito. Sem meia-troca.

## Possibilidades

### `atomic`: as duas formas

| Forma | Quando usar |
| --- | --- |
| Decorador `@transaction.atomic` | A função inteira é uma transação |
| Context manager `with transaction.atomic():` | Só um trecho é transacional |

```python
# como bloco
def view(request):
    do_stuff_outside_transaction()
    with transaction.atomic():
        a.save()
        b.save()          # a+b são atômicos; o resto não
```

!!! info "Fora de `atomic`, cada `save()` já é uma transação"
    O Django roda em *autocommit*: cada operação isolada já é gravada na hora. O
    `atomic` serve para **agrupar** várias operações num único "tudo ou nada".

### Transações aninhadas: savepoints

Pensa como criança: um `atomic` dentro de outro não abre uma transação nova —
cria um **ponto de retorno** (savepoint) dentro da mesma. Se o de dentro falhar,
volta só até ali; o de fora pode continuar.

```python
with transaction.atomic():          # transação externa
    a.save()
    try:
        with transaction.atomic():  # savepoint
            b.save()
            raise ValueError()
    except ValueError:
        pass                         # desfaz só b; a continua válido
    c.save()
```

### `select_for_update`: travar linhas

Pensa como criança: pegar a figurinha na mão para ninguém trocar ela ao mesmo
tempo que você. Bloqueia as linhas até a transação terminar.

```python
with transaction.atomic():
    conta = Account.objects.select_for_update().get(pk=1)
    conta.balance += 100
    conta.save()
```

!!! warning "`select_for_update` exige estar dentro de `atomic`"
    O bloqueio dura até o fim da transação. Fora de um `atomic`, não há
    transação para segurar o bloqueio — o Django levanta erro. E ele **não**
    funciona no SQLite (use PostgreSQL/MySQL para valer).

### `on_commit`: agir só depois que gravou

Pensa como criança: só solte os fogos **depois** que a troca de figurinhas
realmente valeu — não no meio, que pode dar rollback.

```python
from django.db import transaction


def publish(post: Post) -> None:
    """Send a notification only after the DB commit succeeds."""
    with transaction.atomic():
        post.status = "published"
        post.save()
        transaction.on_commit(lambda: send_notification(post.id))   # (1)!
```

1. O e-mail/notificação só dispara **se** a transação for gravada com sucesso.
    Se der rollback, o callback não roda. Evita "enviei e-mail de um post que não
    foi salvo".

!!! danger "Efeitos colaterais externos vão em `on_commit`"
    Mandar e-mail, disparar tarefa Celery, chamar API externa — **depois** do
    commit. Se você fizer isso no meio da transação e ela reverter, o mundo lá
    fora já foi afetado, mas o banco não. `on_commit` resolve.

### Controle manual (raro, mas existe)

| Função | O que faz |
| --- | --- |
| `transaction.set_autocommit(False)` | Desliga o autocommit |
| `transaction.commit()` | Grava manualmente |
| `transaction.rollback()` | Desfaz manualmente |
| `transaction.get_connection().in_atomic_block` | Estou numa transação? |

!!! tip "Prefira `atomic` ao controle manual"
    99% dos casos são resolvidos com `atomic` (decorador ou bloco). Controle
    manual é para situações muito específicas e é fácil de errar.

### `ATOMIC_REQUESTS`: cada requisição numa transação

Você pode envolver **toda** view numa transação, por banco:

```python
DATABASES = {
    "default": {
        # ...
        "ATOMIC_REQUESTS": True,
    }
}
```

Com isso, se a view levantar exceção, tudo que ela gravou é desfeito. Simples,
mas segura uma transação aberta durante a requisição inteira — avalie o custo.

!!! quote "📖 Na documentação oficial"
    - [Database transactions](https://docs.djangoproject.com/en/stable/topics/db/transactions/)

## Recap

- Transação = "tudo ou nada"; erro no meio faz **rollback**.
- `atomic` como decorador (função toda) ou bloco (`with`, só um trecho); fora
  dele, cada `save()` já autocommita.
- `atomic` aninhado vira **savepoint** (volta parcial).
- `select_for_update` trava linhas (dentro de `atomic`, não no SQLite).
- Efeitos externos (e-mail, tarefas) vão em `transaction.on_commit`, para só
  rodarem se o commit valer.
- `ATOMIC_REQUESTS=True` envolve cada view numa transação.

Transações garantem consistência nos dados. Agora os arquivos: os
**[estáticos e media](static-media.md)**.
