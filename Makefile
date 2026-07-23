.PHONY: help install docs-serve docs-build run migrate seed test lint format fix type check

PORT ?= 8000

help:  ## Lista os comandos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install:  ## Instala dependências (app + docs + dev)
	uv sync --all-groups

docs-serve:  ## Sobe o servidor de docs MkDocs (use PORT=8001 para trocar a porta)
	uv run mkdocs serve -a 127.0.0.1:$(PORT)

docs-build:  ## Compila o site de docs em modo estrito
	uv run mkdocs build --strict

run:  ## Sobe o servidor Django (use PORT=8001 para trocar a porta)
	cd example && uv run python manage.py runserver $(PORT)

migrate:  ## Aplica as migrações do banco
	cd example && uv run python manage.py migrate

seed:  ## Popula o blog com dados de exemplo
	cd example && uv run python manage.py seed_blog

test:  ## Roda a suíte de testes
	uv run pytest -q

lint:  ## Verifica lint (ruff), sem alterar
	uv run ruff check .

format:  ## Formata o código (ruff format)
	uv run ruff format .

fix:  ## Aplica todo autofix do ruff + formata
	uv run ruff check --fix .
	uv run ruff format .

type:  ## Checagem de tipos (mypy + django-stubs)
	uv run mypy example

check: lint type test  ## Roda todos os portões (lint + tipos + testes)
