# Testes

Código sem teste é código que você tem medo de mudar. O Django tem ótimo suporte
a testes, e aqui usamos **pytest** com o plugin **pytest-django** — mais conciso
que o `unittest` padrão, com fixtures poderosas.

!!! quote "O que testar num projeto Django"
    - **Modelos** — regras de negócio (o `slug` é gerado? `published_at` é
      carimbado?).
    - **Views** — as páginas respondem? o acesso é protegido?
    - **API** — os endpoints retornam o esperado? a permissão funciona?

## Instalação

```bash
uv add --group dev pytest pytest-django
```

Configuramos o pytest no `pyproject.toml`, apontando o `settings` e onde achar os
testes:

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
python_files = ["test_*.py", "tests.py"]
```

!!! info "Banco de teste automático"
    O `pytest-django` cria um banco **temporário** para os testes e o destrói ao
    final — seu banco de desenvolvimento nunca é tocado. Marque os testes que
    acessam o banco com `@pytest.mark.django_db`.

## Testando um modelo

Verificamos a regra do `save()`: um post publicado ganha `published_at`
automaticamente.

```python
import pytest

from apps.blog.models import Author, Post
from django.contrib.auth import get_user_model


@pytest.fixture
def author(db) -> Author:
    """Create a demo author backed by a user."""
    user = get_user_model().objects.create_user("ana", password="x")
    return Author.objects.create(user=user, display_name="Ana")


@pytest.mark.django_db
def test_publishing_stamps_published_at(author: Author) -> None:
    """Saving a post as PUBLISHED sets ``published_at`` and the slug."""
    post = Post.objects.create(
        title="Olá Mundo", body="...", author=author,
        status=Post.Status.PUBLISHED,
    )
    assert post.slug == "ola-mundo"
    assert post.published_at is not None
    assert post.is_published is True
```

- **`db` / `@pytest.mark.django_db`** — dão acesso ao banco de teste.
- **`@pytest.fixture`** — cria dados reutilizáveis (o `author`) que os testes
  pedem por parâmetro. É a forma pytest de fazer setup.

## Testando o QuerySet customizado

```python
@pytest.mark.django_db
def test_published_manager_excludes_drafts(author: Author) -> None:
    """The ``published()`` queryset returns only published posts."""
    Post.objects.create(title="Draft", body="x", author=author)
    Post.objects.create(
        title="Live", body="x", author=author, status=Post.Status.PUBLISHED,
    )
    assert Post.objects.published().count() == 1
```

## Testando uma view

O **test client** simula requisições HTTP sem subir um servidor:

```python
from django.test import Client


@pytest.mark.django_db
def test_post_list_returns_200(client: Client, author: Author) -> None:
    """The post list page renders successfully."""
    Post.objects.create(
        title="Live", body="x", author=author, status=Post.Status.PUBLISHED,
    )
    response = client.get("/")
    assert response.status_code == 200
    assert b"Live" in response.content


@pytest.mark.django_db
def test_create_view_requires_login(client: Client) -> None:
    """Anonymous users are redirected away from the create page."""
    response = client.get("/posts/new/")
    assert response.status_code == 302
    assert "/login/" in response["Location"]
```

- **`client`** — fixture do pytest-django, já pronta.
- O segundo teste confirma o `LoginRequiredMixin`: anônimo recebe **302** para o
  login. Testar *segurança* é tão importante quanto testar o caminho feliz.

## Testando a API

O DRF traz um `APIClient` que fala JSON:

```python
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_api_list_is_public(author: Author) -> None:
    """Anonymous clients can list published posts."""
    Post.objects.create(
        title="Live", body="x", author=author, status=Post.Status.PUBLISHED,
    )
    response = APIClient().get("/api/posts/")
    assert response.status_code == 200
    assert response.json()["count"] == 1


@pytest.mark.django_db
def test_api_create_requires_auth() -> None:
    """Anonymous clients cannot create posts."""
    response = APIClient().post("/api/posts/", {"title": "X", "body": "Y"})
    assert response.status_code in (401, 403)
```

## Rodando

```bash
uv run pytest             # todos os testes
uv run pytest -v          # verboso
uv run pytest -k list     # só os que casam com "list"
```

!!! tip "Teste o comportamento, não a implementação"
    Bons testes verificam **o que** o sistema faz (a página abre, o rascunho não
    aparece, o anônimo é barrado), não *como* faz por dentro. Assim você pode
    refatorar livremente sem reescrever os testes.

## Recapitulando

- Usamos **pytest + pytest-django**; `DJANGO_SETTINGS_MODULE` no `pyproject.toml`.
- Banco de teste é criado e destruído sozinho; libere com `@pytest.mark.django_db`.
- **Fixtures** criam dados reutilizáveis.
- Teste modelos (regras), views (status + proteção) e a API (`APIClient`).
- Foque no comportamento observável, não nos detalhes internos.

🎉 Você chegou ao fim do guia! Tem um projeto Django completo — tipado, orientado
a objetos, com web, API e testes — e entende **o porquê** de cada peça.
