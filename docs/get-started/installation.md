# Instalação

Nesta página você vai **criar seu próprio projeto Django do zero**, na sua
máquina, do primeiro comando até a tela de boas-vindas do Django rodando no
navegador. Nada de clonar repositório: você digita cada passo e entende o que
cada um faz.

!!! tip "Só quer ver o exemplo pronto rodando?"
    Tem um apêndice no final da página: [Apêndice — rodando o blog de
    exemplo](#apendice-rodando-o-blog-de-exemplo). Mas recomendamos fazer o
    caminho do zero primeiro — é assim que a ficha cai.

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

Instale o `uv`:

=== "Linux / macOS"

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

=== "Windows (PowerShell)"

    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

Confira se funcionou:

```bash
uv --version
```

!!! note "Não precisa instalar Python antes"
    Se a sua máquina não tiver o Python 3.13, o `uv` baixa e usa a versão certa
    automaticamente no passo seguinte. Um problema a menos.

## Passo 1 — criar a pasta do projeto

```bash
uv init meu-blog --python 3.13
cd meu-blog
```

Isso cria a pasta `meu-blog/` com o esqueleto de um projeto Python:

```text
meu-blog/
├── .git/                 # repositório git já inicializado
├── .gitignore
├── .python-version       # trava a versão do Python (3.13)
├── README.md
├── main.py               # arquivo de exemplo — pode apagar
└── pyproject.toml        # onde as dependências são declaradas
```

O `main.py` não serve para nada aqui:

```bash
rm main.py
```

!!! info "O que é o `pyproject.toml`?"
    É a "lista de compras" do projeto: nome, versão do Python exigida e as
    dependências. Quem clonar seu projeto depois só precisa de `uv sync` para
    ter exatamente o mesmo ambiente.

## Passo 2 — instalar o Django

```bash
uv add "django>=6.0,<7"
```

!!! check "O que acabou de acontecer"
    - O `uv` criou a pasta `.venv/` (o ambiente virtual do projeto).
    - Baixou o Python 3.13, se você ainda não tivesse.
    - Instalou o Django e suas dependências (`asgiref`, `sqlparse`).
    - Adicionou `django>=6.0,<7` em `dependencies` no `pyproject.toml`.
    - Criou o `uv.lock` com as versões **exatas** — é ele que garante que o
      ambiente será idêntico em qualquer máquina.

!!! note "Por que `>=6.0,<7`?"
    Aceita qualquer correção e novidade da série 6.x (que são compatíveis entre
    si), mas barra o Django 7, que pode ter mudanças incompatíveis. Você decide
    quando dar esse salto, em vez de ser surpreendido.

Confira a versão instalada:

```bash
uv run django-admin --version
```

!!! note "`uv run`"
    O prefixo `uv run` executa o comando **dentro** do ambiente virtual do
    projeto, sem você precisar "ativar" nada. É equivalente a ativar a `.venv` e
    rodar `python ...`, só que explícito e à prova de esquecimento.

## Passo 3 — criar o projeto Django

```bash
uv run django-admin startproject config .
```

!!! warning "Repare no ponto final"
    O `.` no fim diz "gere aqui, nesta pasta". Sem ele, o Django criaria mais um
    nível (`meu-blog/config/config/...`) — funciona, mas fica aninhado à toa.

Agora a pasta tem:

```text
meu-blog/
├── manage.py             # ponto de entrada de todos os comandos
├── pyproject.toml
├── uv.lock
└── config/               # o "projeto": configuração geral
    ├── __init__.py
    ├── settings.py       # todas as configurações
    ├── urls.py           # roteamento raiz
    ├── asgi.py           # ponto de entrada async (produção)
    └── wsgi.py           # ponto de entrada sync (produção)
```

!!! info "`django-admin` × `manage.py`"
    O `django-admin` é o comando global — usado quando o projeto **ainda não
    existe**. Depois que ele existe, você usa o `manage.py`, que é o mesmo
    programa só que já sabendo qual é o seu `settings.py`.

## Passo 4 — criar o banco de dados

O Django já vem com tabelas próprias (usuários, permissões, sessões, admin).
Elas não existem até você rodar as migrações:

```bash
uv run python manage.py migrate
```

Isso cria o arquivo **`db.sqlite3`** — um banco inteiro em um único arquivo, sem
servidor nenhum para instalar. Perfeito para aprender.

!!! note "Vou ficar preso ao SQLite?"
    Não. Trocar para PostgreSQL é mudar o dicionário `DATABASES` no
    `settings.py` — o resto do código continua igual. É o ORM fazendo o trabalho
    de tradução.

## Passo 5 — subir o servidor

```bash
uv run python manage.py runserver
```

Abra **<http://127.0.0.1:8000/>**. Você deve ver a página de boas-vindas do
Django, com um foguete decolando: *"The install worked successfully!
Congratulations!"* 🚀

!!! check "Se apareceu o foguete"
    Seu Python, seu ambiente virtual, o Django e o servidor de desenvolvimento
    estão todos funcionando. Essa é a base de tudo que vem a seguir.

Para parar o servidor: `Ctrl + C`.

!!! tip "Aviso de migrações pendentes?"
    Se o terminal reclamar de *"unapplied migration(s)"*, é só rodar o
    `migrate` do passo 4 de novo. O `runserver` avisa, mas não aplica sozinho.

## Passo 6 — criar seu usuário administrador

O Django já traz um painel administrativo completo. Para entrar nele, crie um
superusuário:

```bash
uv run python manage.py createsuperuser
```

Ele pergunta usuário, e-mail (opcional) e senha. Com o servidor rodando, acesse
**<http://127.0.0.1:8000/admin/>** e faça login.

!!! note "Está vazio, e está certo"
    Por enquanto o admin só mostra **Users** e **Groups** — as tabelas que o
    próprio Django trouxe. Os seus modelos aparecem lá quando você criá-los e
    registrá-los, no [tutorial de Admin](../tutorial/admin.md).

## Seus próximos passos

Você tem um projeto Django funcionando, criado por você. Daqui em diante o
tutorial constrói um **blog** em cima dessa base, uma página por conceito:

1. **[Configurando o projeto](../tutorial/project-setup.md)** — criar o app
   `blog`, entender `settings.py` e registrar o app.
2. **[Modelos e o ORM](../tutorial/models.md)** — as tabelas do blog.
3. …e assim por diante, até a API REST.

!!! tip "Faça, não copie"
    Digite os comandos e o código no *seu* projeto em vez de só ler. O código de
    referência de cada página vive na pasta
    [`example/`](https://github.com/mauriciobenjamin700/django-survival-guide/tree/main/example)
    do repositório, para você comparar quando algo não bater.

## Apêndice — rodando o blog de exemplo

Se quiser ver o resultado final funcionando (para comparar, ou para explorar o
código pronto), clone o repositório do guia:

```bash
git clone https://github.com/mauriciobenjamin700/django-survival-guide.git
cd django-survival-guide
uv sync
```

O `uv sync` lê o `pyproject.toml` + `uv.lock` e reproduz o ambiente exato:
Django, Django REST Framework e as ferramentas de documentação.

Prepare o banco e popule com dados de demonstração:

```bash
cd example
uv run python manage.py migrate
uv run python manage.py seed_blog
```

O `seed_blog` cria:

- um usuário **`demo`** com senha **`demo12345`**;
- um autor, algumas tags e posts publicados com comentários.

Suba o servidor:

```bash
uv run python manage.py runserver
```

| URL | O que é |
| --- | --- |
| `/` | Lista de posts publicados |
| `/posts/<slug>/` | Detalhe de um post + comentários |
| `/login/` | Login (use `demo` / `demo12345`) |
| `/admin/` | Painel administrativo do Django |
| `/api/` | API REST navegável (guia avançado) |

??? info "Rodando esta documentação localmente"
    A documentação é feita com **MkDocs**. Dentro do repositório clonado:

    ```bash
    uv run mkdocs serve
    ```

    E abra <http://127.0.0.1:8000/>. O normal, porém, é ler a versão publicada
    no GitHub Pages — o link está no topo do repositório.

!!! quote "📖 Na documentação oficial"
    - [Quick install guide](https://docs.djangoproject.com/en/stable/intro/install/)
    - [Writing your first Django app](https://docs.djangoproject.com/en/stable/intro/tutorial01/)
    - [uv documentation](https://docs.astral.sh/uv/)

## Recapitulando

- **uv** gerencia Python, ambiente virtual e dependências: `uv init` cria o
  projeto, `uv add` instala, `uv run <cmd>` executa dentro do ambiente.
- `django-admin startproject config .` gera o projeto (`config/` + `manage.py`).
- `migrate` cria as tabelas iniciais no `db.sqlite3`.
- `runserver` sobe o site em `127.0.0.1:8000` — foguete na tela = tudo certo.
- `createsuperuser` te dá acesso ao `/admin/`.

Com o esqueleto de pé, bora entender como ele é organizado — e criar o app do
blog — em **[Configurando o projeto](../tutorial/project-setup.md)**.
