# Referência: signals

!!! quote "Pensa como criança 🧒"
    Um **signal** é uma campainha. Quando algo acontece numa parte do sistema
    (ex.: "um post foi salvo"), a campainha toca. Quem quiser, deixa combinado
    antes: "quando essa campainha tocar, me avisa que eu faço tal coisa". Assim
    uma parte do código reage a outra **sem** as duas se conhecerem diretamente.

## Caso de uso

Toda vez que um `User` é criado, você quer criar automaticamente o perfil
`Author` dele. Em vez de lembrar de fazer isso em todo lugar que cria usuário,
você "escuta" o sinal de que um usuário foi salvo:

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

Agora, quem quer que crie um usuário (admin, shell, API), o perfil nasce junto.

## Possibilidades

### Os signals que você mais usa

| Signal | Toca quando... |
| --- | --- |
| `pre_save` | Antes de salvar um objeto |
| `post_save` | Depois de salvar (tem `created: bool`) |
| `pre_delete` | Antes de apagar |
| `post_delete` | Depois de apagar |
| `m2m_changed` | Uma relação M2M muda (add/remove/clear) |
| `pre_migrate` / `post_migrate` | Em torno das migrações |
| `request_started` / `request_finished` | Início/fim de requisição |

### Anatomia de um receiver

Pensa como criança: o `@receiver` é o combinado ("me avisa quando..."). A função
é o que você faz quando a campainha toca.

```python
@receiver(post_save, sender=Post)
def on_post_saved(sender, instance, created, **kwargs) -> None:
    """React to a Post being saved."""
    ...
```

| Parâmetro | O que é |
| --- | --- |
| `sender` | A **classe** que enviou o sinal (`Post`) |
| `instance` | O **objeto** salvo/apagado |
| `created` | `True` se foi criação (só `post_save`) |
| `**kwargs` | Sempre inclua — o Django passa extras (`update_fields`, `raw`, etc.) |

!!! warning "`sender=` filtra a campainha"
    Sem `sender=Post`, seu receiver toca para **todos** os modelos salvos no
    projeto. Quase sempre você quer filtrar por um modelo específico.

### Ligar os receivers no `apps.py`

Os receivers só funcionam se o módulo for **importado**. O lugar certo é o
método `ready()` do `AppConfig`:

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

!!! danger "Esqueceu o `ready()`? O signal nunca toca"
    O erro nº 1 com signals: escrever o receiver e ele nunca rodar, porque o
    módulo `signals.py` não foi importado. Importe-o no `ready()`.

### Conectar sem decorador

Alternativa ao `@receiver`, útil para conectar dinamicamente:

```python
from django.db.models.signals import post_save

post_save.connect(create_author_profile, sender=User)
post_save.disconnect(create_author_profile, sender=User)   # desconectar
```

### Signals customizados

Você pode criar a sua própria campainha:

```python
import django.dispatch

post_published = django.dispatch.Signal()      # define

# dispara em algum lugar
post_published.send(sender=Post, post=meu_post)

# escuta
@receiver(post_published)
def notify(sender, post, **kwargs) -> None:
    ...
```

### Quando **evitar** signals

!!! danger "Signals são poderosos e traiçoeiros"
    Eles escondem o fluxo: olhando `user.save()`, você não vê que um `Author`
    nasceu. Isso dificulta ler e depurar. Prefira código **explícito** quando dá:

    - Lógica que pertence ao objeto → sobrescreva `save()` no modelo.
    - Orquestração de várias etapas → faça num **service**/método claro.
    - Reação a evento **de outro app** que você não controla → aí signal brilha.

    Regra: use signal quando **não dá** para colocar a lógica no lugar óbvio.

## Recap

- Signal é uma campainha: algo acontece, receivers combinados reagem —
  desacoplando as partes.
- `post_save`/`pre_save`/`post_delete`/`m2m_changed` são os mais usados;
  `@receiver(signal, sender=Model)` conecta.
- Parâmetros: `sender` (classe), `instance` (objeto), `created` (só post_save),
  sempre `**kwargs`.
- Importe os receivers no `ready()` do `AppConfig`, senão nunca tocam.
- Prefira `save()`/services quando a lógica tem um lugar óbvio; use signals para
  reagir a eventos que você não controla.

Signals reagem no servidor. Já **[sessions e messages](sessions-messages.md)**
guardam estado entre requisições.
