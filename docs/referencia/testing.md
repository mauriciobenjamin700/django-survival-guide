# Referência: testes a fundo

!!! quote "Pensa como criança 🧒"
    Testes são o **cinto de segurança** do código. Você mexe em algo, aperta um
    botão (`pytest`) e ele te avisa na hora se quebrou alguma coisa. Sem isso,
    toda mudança é um pulo no escuro. Com isso, você refatora sem medo.

## Caso de uso

Você quer garantir que um post publicado ganha `published_at`, que a página
abre, e que a API bloqueia quem não está logado. Três testes, com `pytest`:

```python
import pytest
from apps.blog.models import Post


@pytest.mark.django_db
def test_publishing_stamps_date(author) -> None:
    """Publishing a post stamps published_at."""
    post = Post.objects.create(
        title="Olá", body="x", author=author, status=Post.Status.PUBLISHED
    )
    assert post.published_at is not None
```

## Possibilidades

### pytest-django × unittest

| | `pytest` + pytest-django | `unittest` (Django `TestCase`) |
| --- | --- | --- |
| Estilo | Funções + fixtures | Classes + métodos `setUp` |
| Banco | `@pytest.mark.django_db` | Automático em `TestCase` |
| Verbosidade | Menor | Maior |

Neste guia usamos **pytest**: mais enxuto e com fixtures poderosas.

### Configuração

```toml
# pyproject.toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
pythonpath = ["example"]
python_files = ["test_*.py", "tests.py"]
```

### Acesso ao banco: `django_db`

!!! danger "Sem a marca, o teste não toca no banco"
    Por segurança, o pytest-django **bloqueia** o banco por padrão. Marque com
    `@pytest.mark.django_db` (ou peça a fixture `db`) os testes que precisam dele.
    Esqueceu? O erro é `Database access not allowed`.

O banco de teste é criado e destruído sozinho — seu `db.sqlite3` real nunca é
tocado.

### Fixtures: dados reutilizáveis

Pensa como criança: uma fixture é um "brinquedo já montado" que qualquer teste
pode pedir só citando o nome no parâmetro.

```python
# conftest.py — visível para todos os testes ao redor
import pytest
from django.contrib.auth import get_user_model
from apps.blog.models import Author


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user("ana", password="x")


@pytest.fixture
def author(user):
    return Author.objects.create(user=user, display_name="Ana")
```

| Recurso | Papel |
| --- | --- |
| `conftest.py` | Fixtures compartilhadas (sem importar) |
| `@pytest.fixture` | Define um dado/recurso reutilizável |
| Fixtures pedem fixtures | `author` recebe `user` — compõem |
| `scope="session"` | Cria uma vez para toda a sessão de testes |

### Clientes de teste

=== "Views (HTML) — `client`"

    ```python
    def test_home(client, published_post):
        response = client.get("/")
        assert response.status_code == 200

    def test_login_required(client):
        response = client.get("/posts/new/")
        assert response.status_code == 302

    def test_authed(client, user):
        client.force_login(user)         # atalho: loga sem senha
        assert client.get("/posts/new/").status_code == 200
    ```

=== "API (JSON) — `APIClient`"

    ```python
    from rest_framework.test import APIClient

    def test_api_public(published_post):
        r = APIClient().get("/api/posts/")
        assert r.status_code == 200
        assert r.json()["count"] == 1

    def test_api_auth(user):
        c = APIClient()
        c.force_authenticate(user=user)
        r = c.post("/api/posts/", {"title": "X", "body": "Y"}, format="json")
        assert r.status_code == 201
    ```

| Cliente | Para |
| --- | --- |
| `client` (fixture) | Views HTML |
| `APIClient` (DRF) | Endpoints JSON |
| `.force_login(user)` | Logar sem passar pela tela |
| `.force_authenticate(user=...)` | Autenticar na API |

### Contar queries: `django_assert_num_queries`

Pensa como criança: conta quantas vezes o teste "abriu a caixa" do banco — pega
o N+1 no flagrante.

```python
def test_list_is_efficient(client, django_assert_num_queries, published_post):
    """The list page must not explode into N+1 queries."""
    with django_assert_num_queries(3):
        client.get("/")
```

### Mocking: fingir o mundo externo

Não teste e-mail/HTTP de verdade — finja:

```python
from unittest.mock import patch


@patch("apps.blog.services.send_notification")
def test_publish_notifies(mock_send, author):
    """Publishing triggers a notification (mocked)."""
    Post.objects.create(title="X", body="y", author=author,
                        status=Post.Status.PUBLISHED)
    # ... aciona a lógica ...
    mock_send.assert_called_once()
```

!!! tip "Faça mock de onde é USADO, não de onde é definido"
    Use `@patch("apps.blog.services.send_notification")` (o caminho onde o código
    **importa/usa**), não `@patch("email_lib.send")`. Errar o caminho é o motivo
    nº 1 de "meu mock não pegou".

### Parametrizar: um teste, vários casos

```python
import pytest


@pytest.mark.parametrize("status,expected", [
    ("published", 200),
    ("draft", 404),
])
@pytest.mark.django_db
def test_visibility(client, author, status, expected):
    post = Post.objects.create(title="X", body="y", author=author, status=status)
    assert client.get(f"/posts/{post.slug}/").status_code == expected
```

### Rodar e medir cobertura

```bash
uv run pytest                       # tudo
uv run pytest -v                    # verboso
uv run pytest -k api                # só os que casam "api"
uv run pytest -x                    # para no primeiro erro
uv run pytest --cov=apps            # cobertura (precisa pytest-cov)
```

!!! tip "Teste comportamento, não implementação"
    Bons testes checam **o que** acontece (a página abre, o rascunho some, o
    anônimo é barrado), não *como* por dentro. Assim você refatora livre sem
    reescrever os testes.

!!! quote "📖 Na documentação oficial"
    - [Testing in Django](https://docs.djangoproject.com/en/stable/topics/testing/)
    - [pytest-django](https://pytest-django.readthedocs.io/)

## Recap

- pytest + pytest-django; libere o banco com `@pytest.mark.django_db` (banco de
  teste é isolado e descartável).
- **Fixtures** em `conftest.py` montam dados reutilizáveis e compõem entre si.
- `client` (HTML) e `APIClient` (JSON); `force_login`/`force_authenticate`.
- `django_assert_num_queries` pega N+1; `@patch` finge o mundo externo (patch no
  caminho de **uso**); `parametrize` roda vários casos.
- Foque no comportamento observável; meça com `--cov`.

Fechando o ciclo das views: as **[generic views e mixins](generic-views.md)**.
