# Referência: management commands

!!! quote "Pensa como criança 🧒"
    Você já usa comandos prontos: `migrate`, `runserver`, `createsuperuser`. Um
    **management command** é um botão desses que **você** cria. É um programinha
    que roda pelo terminal, já com acesso a todo o seu projeto (banco, modelos,
    settings) — perfeito para tarefas fora do site: importar dados, limpar
    lixo, enviar um relatório.

## Caso de uso

Você quer popular o blog com dados de teste rodando `python manage.py seed_blog`.
Criar um comando é escrever uma classe `Command` com um método `handle`:

```python
# apps/blog/management/commands/seed_blog.py
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.blog.models import Post


class Command(BaseCommand):
    """Seed the blog with demo data."""

    help = "Popula o blog com dados de exemplo."

    @transaction.atomic
    def handle(self, *args: object, **options: object) -> None:
        """Run the command."""
        Post.objects.get_or_create(title="Olá Mundo", defaults={"body": "..."})
        self.stdout.write(self.style.SUCCESS("Dados criados!"))
```

Onde o arquivo fica **importa**: `app/management/commands/<nome>.py`. O nome do
arquivo vira o nome do comando.

## Possibilidades

### A estrutura de pastas (obrigatória)

```text
apps/blog/
└── management/
    ├── __init__.py                 # precisa existir
    └── commands/
        ├── __init__.py             # precisa existir
        └── seed_blog.py            # -> python manage.py seed_blog
```

!!! danger "Faltou um `__init__.py`? O comando não aparece"
    O Django só descobre comandos em `management/commands/` **se** ambas as
    pastas tiverem `__init__.py` e o app estiver em `INSTALLED_APPS`. Comando
    "não encontrado" quase sempre é isso.

### Atributos e métodos da classe

| Membro | Papel |
| --- | --- |
| `help` | Texto exibido em `manage.py <cmd> --help` |
| `handle(self, *args, **options)` | O corpo do comando (obrigatório) |
| `add_arguments(self, parser)` | Declara argumentos/opções |
| `self.stdout` / `self.stderr` | Saída (use em vez de `print`) |
| `self.style` | Cores: `SUCCESS`, `WARNING`, `ERROR`, `NOTICE` |

### Recebendo argumentos

Pensa como criança: o `add_arguments` é onde você diz quais "peças de LEGO" o
comando aceita; elas chegam em `options` no `handle`.

```python
class Command(BaseCommand):
    help = "Apaga posts em rascunho mais antigos que N dias."

    def add_arguments(self, parser) -> None:
        """Declare command-line arguments."""
        parser.add_argument("days", type=int, help="Idade mínima em dias")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Só mostra, não apaga",
        )

    def handle(self, *args: object, **options: object) -> None:
        """Delete (or preview) old draft posts."""
        days: int = options["days"]
        dry_run: bool = options["dry_run"]
        qs = Post.objects.filter(status="draft").older_than(days)

        if dry_run:
            self.stdout.write(self.style.NOTICE(f"{qs.count()} seriam apagados."))
            return

        deleted, _ = qs.delete()
        self.stdout.write(self.style.SUCCESS(f"{deleted} apagados."))
```

Uso:

```bash
python manage.py cleanup_drafts 30 --dry-run
python manage.py cleanup_drafts 30
```

| `add_argument` | Tipo de argumento |
| --- | --- |
| `parser.add_argument("nome")` | Posicional obrigatório |
| `parser.add_argument("--flag", action="store_true")` | Opção booleana |
| `parser.add_argument("--n", type=int, default=10)` | Opção com valor |
| `parser.add_argument("ids", nargs="+", type=int)` | Vários valores |

### Boas práticas

!!! tip "Use `self.stdout.write`, não `print`"
    `self.stdout.write(...)` respeita redirecionamento, testes e o `--verbosity`.
    `print` fura tudo isso. Para cores, embrulhe com `self.style.SUCCESS(...)`.

!!! tip "Envolva escritas no banco em `@transaction.atomic`"
    Se o comando faz muitas alterações e algo falha no meio, a transação
    garante "tudo ou nada" — sem deixar o banco pela metade.

### Testando um comando

```python
from io import StringIO
from django.core.management import call_command


def test_seed_creates_posts(db) -> None:
    out = StringIO()
    call_command("seed_blog", stdout=out)
    assert "Dados criados" in out.getvalue()
    assert Post.objects.exists()
```

### Comandos embutidos que valem conhecer

| Comando | Para quê |
| --- | --- |
| `shell` / `shell_plus` | Console Python com o projeto carregado |
| `dbshell` | Console do banco |
| `dumpdata` / `loaddata` | Exporta/importa dados (fixtures) |
| `collectstatic` | Junta arquivos estáticos (deploy) |
| `createsuperuser` | Cria admin |
| `check` | Valida o projeto |
| `showmigrations` | Lista migrações |

!!! quote "📖 Na documentação oficial"
    - [Writing custom django-admin commands](https://docs.djangoproject.com/en/stable/howto/custom-management-commands/)

## Recap

- Management command = um `manage.py <cmd>` que você cria; roda com o projeto
  todo carregado.
- Arquivo em `app/management/commands/<nome>.py`; **ambos** os `__init__.py`
  precisam existir.
- Classe `Command`: `help`, `handle()`, `add_arguments(parser)`; saída por
  `self.stdout.write` + `self.style.*` (nunca `print`).
- Argumentos via `parser.add_argument` (posicionais, `--flags`, `nargs`).
- Envolva escritas em `@transaction.atomic`; teste com `call_command`.

Com tudo pronto, falta pôr no ar: o **[deploy](deploy.md)**.
