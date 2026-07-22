# Instalação

Vamos preparar o ambiente e deixar o projeto de exemplo rodando na sua máquina.

## Pré-requisitos

Você precisa de:

- **Python 3.13 ou superior** (o guia mira 3.14).
- **[uv](https://docs.astral.sh/uv/)** — gerenciador de pacotes e versões de
  Python, rápido e moderno. É o que usamos em vez de `pip` + `venv` manuais.

!!! info "Por que uv?"
    O `uv` resolve dependências, cria o ambiente virtual e até baixa a versão
    certa do Python — tudo com um comando e de forma reprodutível (via
    `uv.lock`). Sem mágica: um arquivo `pyproject.toml` declara o que o projeto
    precisa, e o `uv` cuida do resto.

Instale o `uv` (Linux/macOS):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Clonando o projeto

```bash
git clone https://github.com/mauriciobenjamin700/django-survival-guide.git
cd django-survival-guide
```

## Instalando as dependências

Um único comando cria o ambiente virtual e instala tudo que está no
`pyproject.toml`:

```bash
uv sync
```

!!! check "O que acabou de acontecer"
    - O `uv` leu o `pyproject.toml`, baixou o Python correto (se preciso) e
      criou a pasta `.venv/`.
    - Instalou Django, o Django REST Framework e as ferramentas de documentação.
    - Travou as versões exatas em `uv.lock`, para o ambiente ser idêntico em
      qualquer máquina.

## Preparando o banco e os dados de exemplo

O exemplo usa **SQLite** — um banco em um único arquivo, sem servidor. Perfeito
para aprender. Entre na pasta do projeto e rode as migrações:

```bash
cd example
uv run python manage.py migrate
```

Depois, popule o blog com dados de demonstração:

```bash
uv run python manage.py seed_blog
```

!!! note "`uv run`"
    O prefixo `uv run` executa o comando **dentro** do ambiente virtual do
    projeto, sem você precisar "ativar" nada. É equivalente a ativar a `.venv` e
    rodar `python ...`, só que explícito e à prova de esquecimento.

Esse comando cria:

- um usuário **`demo`** com senha **`demo12345`**;
- um autor, algumas tags e posts publicados com comentários.

## Rodando o servidor

```bash
uv run python manage.py runserver
```

Abra **<http://127.0.0.1:8000/>** no navegador. Você deve ver a lista de posts. 🎉

| URL | O que é |
| --- | --- |
| `/` | Lista de posts publicados |
| `/posts/<slug>/` | Detalhe de um post + comentários |
| `/login/` | Login (use `demo` / `demo12345`) |
| `/admin/` | Painel administrativo do Django |
| `/api/` | API REST navegável (guia avançado) |

!!! tip "Acessando o admin"
    Para entrar em `/admin/`, crie um superusuário:
    ```bash
    uv run python manage.py createsuperuser
    ```

## Rodando a documentação localmente (opcional)

Esta documentação é feita com **MkDocs**. Para vê-la localmente:

```bash
uv run mkdocs serve
```

E abra <http://127.0.0.1:8000/>. Mas o normal é ler a versão publicada no
GitHub Pages — o link está no topo do repositório.

## Recapitulando

- Usamos **uv** para gerenciar Python e dependências sem passos manuais.
- `uv sync` instala tudo; `uv run <cmd>` executa dentro do ambiente.
- `migrate` cria as tabelas; `seed_blog` popula dados de exemplo.
- `runserver` sobe o site em `127.0.0.1:8000`.

Com o projeto rodando, bora entender como ele é montado — começando pela
**[configuração do projeto](../tutorial/project-setup.md)**.
