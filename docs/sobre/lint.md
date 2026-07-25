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

Esse comando instala o Ruff e registra ele no grupo `dev` do seu
`pyproject.toml`. Instalado, ele ainda não sabe **quais** regras você quer — isso
vem da configuração.

### Onde colocar a configuração

Abra o arquivo `pyproject.toml` que fica na **raiz do projeto** (mesma pasta do
`Makefile`, um nível acima do `example/`) e **cole os blocos abaixo no final do
arquivo**:

```toml
# pyproject.toml  ← cole isto no final do arquivo
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

!!! info "O `pyproject.toml` é o painel de controle do projeto"
    Cada bloco `[alguma.coisa]` é uma **seção** desse painel: `[tool.ruff]`
    configura o Ruff, `[tool.mypy]` configura o mypy, `[project]` descreve o seu
    pacote. A ordem das seções não importa — mas **não repita** uma seção que já
    existe: se você já tem um `[tool.ruff]` no arquivo, edite o que está lá em vez
    de colar um segundo.

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

Ainda no `pyproject.toml`, logo abaixo do bloco `[tool.ruff.lint]` que você colou:

```toml
# pyproject.toml
[tool.ruff.lint.per-file-ignores]
"**/tests/*" = ["S101", "ANN"]        # asserts e tipos livres nos testes
"**/__init__.py" = ["F401"]           # re-exports não são "imports não usados"
"**/settings.py" = ["E501"]           # algumas linhas de config são longas
```

## Antes do ritual: o `Makefile`

Daqui pra frente aparecem comandos como `make fix` e `make check`. Eles **não
vêm** do Python, do `uv` nem do Ruff — vêm de um arquivo chamado `Makefile`, que
**você mesmo escreve** na raiz do projeto. Ele é só uma lista de atalhos com
nome: `make fix` quer dizer "executa o que está escrito na receita `fix`".

!!! quote "Pensa como criança 🧒"
    O `Makefile` é a **cola grudada na porta da geladeira**. Em vez de lembrar a
    receita inteira toda vez ("mistura, bate, assa 40 min"), você escreve uma vez
    e dá um nome: *bolo*. Depois só grita o nome. `make fix` é gritar o nome da
    receita — o computador lembra os passos.

### 1. Crie o arquivo

Na **raiz do projeto** (mesma pasta do `pyproject.toml`), crie um arquivo chamado
exatamente `Makefile` — com `M` maiúsculo e **sem extensão** (não é
`Makefile.txt`):

```text
meu-projeto/
├── Makefile          # ← crie este arquivo
├── pyproject.toml
├── manage.py
├── config/           # settings.py, urls.py, wsgi.py
└── apps/
    └── blog/
```

O `make` procura o `Makefile` na pasta onde você está — por isso os comandos
`make ...` só funcionam quando você está na **raiz do projeto** (a pasta do
`manage.py`).

### 2. Cole este conteúdo

```make
.PHONY: help lint format fix type test check

help:  ## Lista os comandos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

lint:  ## Verifica lint (ruff), sem alterar
	uv run ruff check .

format:  ## Formata o código (ruff format)
	uv run ruff format .

fix:  ## Aplica todo autofix do ruff + formata
	uv run ruff check --fix .
	uv run ruff format .

type:  ## Checagem de tipos (mypy + django-stubs)
	uv run mypy apps config

test:  ## Roda a suíte de testes
	uv run pytest -q

check: lint type test  ## Roda todos os portões (lint + tipos + testes)
```

Lendo isso em voz alta: cada `nome:` é uma **receita** (chamada *target*), e as
linhas indentadas abaixo dela são os comandos que ela executa. O `check: lint
type test` não tem comandos próprios — ele só diz "roda essas três receitas, nessa
ordem". O `## texto` depois dos dois-pontos é a descrição que o `make help`
imprime.

!!! warning "Ajuste os caminhos para **o seu** projeto"
    O Ruff (`lint`, `format`, `fix`) recebe `.` — a pasta atual — então funciona em
    qualquer projeto sem ajuste. O **mypy é diferente**: você passa quais pastas
    ele deve checar. Acima estão `apps config`, que é o layout que este guia
    ensina:

    | O que você tem | O que passar pro mypy |
    | --- | --- |
    | `apps/` + `config/` na raiz (este guia) | `uv run mypy apps config` |
    | tudo na raiz, sem `apps/` | `uv run mypy .` |
    | app único, ex.: `blog/` + `config/` | `uv run mypy blog config` |
    | projeto dentro de uma subpasta, ex.: `src/` | `uv run mypy src` |

    Passar `.` também funciona e ainda cobre o `manage.py` — o mypy ignora a
    `.venv` sozinho. As migrations ficam de fora pelo `exclude` (próxima seção).
    Se o comando reclamar de módulo não encontrado, o problema é o `mypy_path`,
    não a lista de pastas.

!!! note "Neste repositório os caminhos são outros"
    O guia mantém o projeto de exemplo dentro de `example/`, então o
    [`Makefile` do repo](https://github.com/mauriciobenjamin700/django-survival-guide/blob/main/Makefile)
    usa `uv run mypy example` e os comandos do Django rodam com `cd example`. No
    **seu** projeto o `manage.py` está na raiz — não copie o `example/`.

!!! danger "Indentação do `Makefile` é TAB, não espaço"
    Essa é a pegadinha clássica: as linhas de comando **precisam** começar com um
    caractere **TAB**. Se o seu editor converter TAB em espaços, o `make` falha
    com:

    ```text
    Makefile:5: *** missing separator.  Stop.
    ```

    No VS Code, abra o `Makefile` e clique em **Spaces: 4** na barra de baixo →
    **Indent Using Tabs**. Copiando o bloco acima daqui, o TAB já vem junto — mas
    confira se der erro.

### 3. Teste

```bash
make help
```

Deve listar os comandos com as descrições. A partir daí, os atalhos funcionam:

```bash
make fix        # = ruff check --fix .  &&  ruff format .
```

!!! tip "O `Makefile` cresce com o projeto"
    Este é o mínimo para lint e tipos. O `Makefile` deste guia também tem
    `make install`, `make run`, `make migrate`, `make seed`, `make docs-serve` —
    olhe o [`Makefile` na raiz do
    repositório](https://github.com/mauriciobenjamin700/django-survival-guide/blob/main/Makefile)
    para copiar o conjunto completo. A regra é: **todo comando que você digita
    duas vezes merece uma receita**.

## O ritual: `make fix`

Um comando arruma tudo que dá para arrumar (imports, aspas, espaços, código
morto) e formata:

```bash
make fix
```

E os portões que **checam sem alterar** (para CI e pré-commit):

| Comando | Faz |
| --- | --- |
| `make lint` | `ruff check .` — aponta problemas |
| `make format` | `ruff format .` — formata |
| `make fix` | autofix + format (o "conserto") |
| `make type` | `mypy apps config` — checa tipos |
| `make check` | lint + type + test (todos os portões) |

### Não tenho o `make` (ou estou no Windows)

O `make` já vem no macOS (com as *Command Line Tools*) e na maioria das distros
Linux. Se `make help` responder `command not found`:

=== "Linux (Debian/Ubuntu)"

    ```bash
    sudo apt install make
    ```

=== "macOS"

    ```bash
    xcode-select --install
    ```

=== "Windows"

    Use o **WSL** (recomendado, é o ambiente deste guia) ou instale via
    [Chocolatey](https://chocolatey.org/):

    ```powershell
    choco install make
    ```

E se você não quiser instalar nada, **nenhum comando aqui depende do `make`** —
ele só encurta. Os equivalentes diretos:

| Atalho | Comando real |
| --- | --- |
| `make lint` | `uv run ruff check .` |
| `make format` | `uv run ruff format .` |
| `make fix` | `uv run ruff check --fix . && uv run ruff format .` |
| `make type` | `uv run mypy apps config` |
| `make test` | `uv run pytest -q` |
| `make check` | os três de cima, em sequência |

## Tipos: mypy + django-stubs

O Ruff **exige** anotações; o [mypy](https://mypy.readthedocs.io/) **verifica** se
elas batem. Para o mypy entender o Django (managers, campos, `settings`), usamos o
`django-stubs`.

```bash
uv add --group dev mypy django-stubs djangorestframework-stubs
```

E, de novo, no final do `pyproject.toml`:

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.13"
plugins = ["mypy_django_plugin.main", "mypy_drf_plugin.main"]
mypy_path = "."                                   # (1)!
check_untyped_defs = true
exclude = ['migrations/']

[tool.django-stubs]
django_settings_module = "config.settings"        # (2)!
```

1. **Onde o mypy procura os seus módulos.** Use a pasta que contém o `manage.py`
   — no layout deste guia, a própria raiz (`"."`). Se o seu projeto vive numa
   subpasta (`src/`, `backend/`, ou o `example/` deste repo), aponte para ela:
   `mypy_path = "src"`. Errar isso dá `Cannot find implementation or library stub
   for module named "apps.blog"`.
2. **O caminho de import do seu settings** — exatamente o que está no
   `manage.py`/`DJANGO_SETTINGS_MODULE`. Com `config/settings.py` fica
   `"config.settings"`; se você separou por ambiente (`config/settings/dev.py`),
   fica `"config.settings.dev"`. O plugin **importa** esse módulo para ler seus
   models — settings errado = mypy não roda.

!!! warning "mypy com Django exige o plugin + stubs"
    Sem `django-stubs` e o plugin, o mypy reclama de coisas que **são** corretas
    no Django (ex.: `objects`, tipos de campo). O plugin ensina o mypy a "ler"
    Django. As migrations ficam de fora pelo `exclude` — são geradas, não faz
    sentido checar.

!!! tip "Confira antes de seguir"
    ```bash
    make type        # ou: uv run mypy apps config
    ```

    Erros de tipo no seu código são esperados (é para isso que ele existe). O que
    **não** deve aparecer é `Cannot find implementation`, `django_settings_module
    is not set` ou `ImproperlyConfigured` — esses três são configuração errada nos
    dois pontos acima, não problema no seu código.

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
- **Ruff** faz lint + imports + formatação num só (rápido); a config vai em blocos
  `[tool.ruff...]` colados no **`pyproject.toml`**, com `select` amplo (inclui
  `ANN` para tipagem) e `ignore`/`per-file-ignores` com critério; **exclua
  migrations**.
- Os comandos `make ...` vêm de um **`Makefile`** que você cria na raiz — atalhos
  com nome, indentados com **TAB**. Sem `make`, rode os comandos `uv run ...`
  direto.
- O ritual é `make fix` (conserta) e `make check` (lint + tipos + testes).
- **mypy + django-stubs** verificam os tipos que o Ruff exige — e aqui os caminhos
  são **seus**: quais pastas checar (`mypy apps config`), `mypy_path` apontando
  para a pasta do `manage.py` e `django_settings_module` no caminho de import do
  seu settings.
- Convenções: aspas duplas, tipar tudo, docstrings, imports absolutos, sem
  comentário inline.

!!! quote "📖 Na documentação oficial"
    - [Ruff](https://docs.astral.sh/ruff/)
    - [mypy](https://mypy.readthedocs.io/)
    - [django-stubs](https://github.com/typeddjango/django-stubs)

Veja também como contribuir seguindo esses padrões em
**[Contribuindo](contribuindo.md)**.
