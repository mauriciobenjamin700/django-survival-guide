# Lint e boas práticas

Código de estudo é lido por muita gente — então precisa ser **consistente** e
**legível**. Em vez de discutir estilo em cada revisão, deixamos uma ferramenta
cuidar disso automaticamente. Esta página mostra o setup que este projeto usa e
recomenda.

!!! quote "Pensa como criança 🧒"
    O **linter** é o professor que corrige a redação: aponta erro de vírgula,
    palavra repetida, frase torta — e ainda arruma sozinho o que dá. Você para de
    perder tempo com detalhe e foca na ideia. E como o professor é sempre o mesmo,
    todo mundo escreve do mesmo jeito.

## Uma ferramenta para tudo: Ruff

O [Ruff](https://docs.astral.sh/ruff/) faz, muito rápido, o que antes exigia
várias ferramentas (flake8 + isort + black + pyupgrade): **lint**, **ordenação de
imports** e **formatação** — num binário só.

```bash
uv add --group dev ruff
```

```toml
# pyproject.toml
[tool.ruff]
line-length = 88
target-version = "py313"
extend-exclude = ["**/migrations/*"]      # (1)!

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "N", "SIM", "RUF", "ANN"]
ignore = ["ANN401", "ANN002", "ANN003", "RUF012"]

[tool.ruff.format]
quote-style = "double"                     # (2)!
indent-style = "space"
```

1. **Migrações são geradas** pelo Django — não faz sentido lintar. Sempre exclua.
2. Aspas duplas em todo lugar, sem discussão.

### O que cada grupo de regras pega

| Código | Regras |
| --- | --- |
| `E`/`W` | Estilo PEP 8 (espaços, linhas) |
| `F` | Erros reais (variável não usada, import faltando) |
| `I` | Ordenação de imports (stdlib → terceiros → local) |
| `B` | Bugs prováveis (flake8-bugbear) |
| `C4` | Comprehensions mais limpas |
| `UP` | Moderniza sintaxe (pyupgrade) |
| `N` | Nomes (PascalCase p/ classe, snake_case p/ função) |
| `SIM` | Simplificações (`if` redundante etc.) |
| `ANN` | Exige **anotações de tipo** |
| `RUF` | Regras próprias do Ruff |

!!! tip "Por que ligar o `ANN` (tipagem)"
    O `ANN` força você a anotar funções e métodos. Isso é o nosso princípio de
    *tipagem clara* virando regra automática — o editor te ajuda e o leitor
    entende a intenção. Ignoramos só `ANN401` (permitir `Any` explícito) e as
    anotações de `*args`/`**kwargs`, que só geram ruído.

### Ignorar por arquivo (com critério)

```toml
[tool.ruff.lint.per-file-ignores]
"**/tests/*" = ["S101", "ANN"]        # asserts e tipos livres nos testes
"**/__init__.py" = ["F401"]           # re-exports não são "imports não usados"
"**/settings.py" = ["E501"]           # algumas linhas de config são longas
```

## O ritual: `make fix`

Um comando arruma tudo que dá para arrumar (imports, aspas, espaços, código
morto) e formata:

```bash
make fix        # = ruff check --fix .  &&  ruff format .
```

E os portões que **checam sem alterar** (para CI e pré-commit):

| Comando | Faz |
| --- | --- |
| `make lint` | `ruff check .` — aponta problemas |
| `make format` | `ruff format .` — formata |
| `make fix` | autofix + format (o "conserto") |
| `make type` | `mypy example` — checa tipos |
| `make check` | lint + type + test (todos os portões) |

## Tipos: mypy + django-stubs

O Ruff **exige** anotações; o [mypy](https://mypy.readthedocs.io/) **verifica** se
elas batem. Para o mypy entender o Django (managers, campos, `settings`), usamos o
`django-stubs`.

```bash
uv add --group dev mypy django-stubs djangorestframework-stubs
```

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.13"
plugins = ["mypy_django_plugin.main", "mypy_drf_plugin.main"]
mypy_path = "example"
check_untyped_defs = true

[tool.django-stubs]
django_settings_module = "config.settings"
```

!!! warning "mypy com Django exige o plugin + stubs"
    Sem `django-stubs` e o plugin, o mypy reclama de coisas que **são** corretas
    no Django (ex.: `objects`, tipos de campo). O plugin ensina o mypy a "ler"
    Django. Migrations e testes ficam de fora (`ignore_errors`).

## As convenções que o lint reforça

Além das regras automáticas, seguimos convenções que fazem o código respirar:

- **Aspas duplas** sempre (`"texto"`).
- **Tipar tudo**: parâmetros, retornos, atributos.
- **Docstrings** Google-style nas classes/métodos (em inglês, no nosso caso).
- **Imports absolutos**, agrupados (o `I` do Ruff ordena).
- **Sem comentário inline** explicando o *porquê* — isso vai na **docstring**. O
  código diz *o quê*; a docstring diz *por quê*.

!!! tip "Rode antes de todo commit"
    O hábito: `make fix` (arruma) → `make check` (garante). Para automatizar,
    configure um **pre-commit** que roda `ruff check --fix` e `ruff format` em
    cada commit — aí ninguém esquece.

## Recapitulando

- Um linter mantém o código consistente e legível sem discussão manual.
- **Ruff** faz lint + imports + formatação num só (rápido); config com `select`
  amplo (inclui `ANN` para tipagem) e `ignore`/`per-file-ignores` com critério;
  **exclua migrations**.
- O ritual é `make fix` (conserta) e `make check` (lint + tipos + testes).
- **mypy + django-stubs** verificam os tipos que o Ruff exige.
- Convenções: aspas duplas, tipar tudo, docstrings, imports absolutos, sem
  comentário inline.

!!! quote "📖 Na documentação oficial"
    - [Ruff](https://docs.astral.sh/ruff/)
    - [mypy](https://mypy.readthedocs.io/)
    - [django-stubs](https://github.com/typeddjango/django-stubs)

Veja também como contribuir seguindo esses padrões em
**[Contribuindo](contribuindo.md)**.
