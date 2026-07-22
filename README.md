# Django Survival Guide 🐍

> 📖 **Documentação (site):** **[Português](https://mauriciobenjamin700.github.io/django-survival-guide/)** · **[English](https://mauriciobenjamin700.github.io/django-survival-guide/en/)**

Um guia para aprender **Django moderno** do zero — com **tipagem clara**,
**orientação a objetos** e **zero mágica**. No estilo didático e progressivo da
[documentação do FastAPI](https://fastapi.tiangolo.com): um conceito por página,
exemplos completos e prontos para rodar, e o **porquê** de cada peça.

## O que tem aqui

- **`docs/`** — o guia em si, bilíngue (PT-BR padrão + EN), publicado no GitHub Pages.
- **`example/`** — um blog Django **completo e rodável** que evolui ao longo do guia:
  do Django puro (models, admin, ORM, views baseadas em classe, templates,
  formulários, autenticação) até uma **API REST** com o Django REST Framework.

```text
Post ──< Comment      (um post tem vários comentários)
Post >── Author       (cada post tem um autor)
Post >──< Tag         (posts e tags: muitos-para-muitos)
```

## Versões

| Ferramenta | Versão |
| --- | --- |
| Python | 3.14 (alvo) · o exemplo roda em 3.13+ |
| Django | 6.0 |
| Django REST Framework | 3.17 |
| uv | 0.7+ |

## Começando rápido

Pré-requisitos: **Python 3.13+** e **[uv](https://docs.astral.sh/uv/)**.

```bash
# 1. Clonar e instalar
git clone https://github.com/mauriciobenjamin700/django-survival-guide.git
cd django-survival-guide
uv sync

# 2. Preparar o banco e dados de exemplo
cd example
uv run python manage.py migrate
uv run python manage.py seed_blog        # usuário demo / demo12345

# 3. Rodar
uv run python manage.py runserver
```

Abra <http://127.0.0.1:8000/>. Rotas principais:

| URL | O que é |
| --- | --- |
| `/` | Lista de posts |
| `/posts/<slug>/` | Detalhe + comentários |
| `/login/` | Login (`demo` / `demo12345`) |
| `/admin/` | Painel administrativo |
| `/api/` | API REST navegável (DRF) |

## Rodando os testes

```bash
uv run pytest
```

## Documentação localmente

```bash
uv run mkdocs serve
```

O normal, porém, é ler a versão publicada — os links de PT e EN estão no topo
deste README.

## Estrutura

```text
django-survival-guide/
├── docs/                       # guia MkDocs (PT padrão + .en.md)
├── example/                    # blog Django rodável
│   ├── config/                 # settings, urls, wsgi/asgi
│   ├── apps/blog/              # models, views (CBV), forms, admin, api/, tests/
│   └── manage.py
├── mkdocs.yml
└── pyproject.toml              # gerenciado com uv
```

## Licença

MIT.
