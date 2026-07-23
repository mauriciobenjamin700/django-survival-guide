# Contribuindo

Quer melhorar o guia — corrigir um erro, traduzir, adicionar uma página? Ótimo!
Este documento mostra como rodar o projeto e quais padrões seguir.

## Preparar o ambiente

```bash
git clone https://github.com/mauriciobenjamin700/django-survival-guide.git
cd django-survival-guide
uv sync --all-groups          # app + dev + docs + prod
```

## Rodar as coisas

| Objetivo | Comando |
| --- | --- |
| Servidor do blog | `make run` (ou `cd example && uv run python manage.py runserver`) |
| Testes | `make test` (ou `uv run pytest`) |
| Docs local | `make docs-serve` |
| Build das docs (estrito) | `make docs-build` |

!!! danger "O build das docs precisa passar em `--strict`"
    Antes de abrir um PR, rode `make docs-build`. Ele roda
    `mkdocs build --strict`: **qualquer** warning vira erro. Link quebrado,
    página fora do `nav`, referência que não resolve — tudo barra aqui.

## Padrões da documentação

Este guia segue o estilo da [documentação do FastAPI](https://fastapi.tiangolo.com):

- **Um conceito por página**, na ordem de aprendizado.
- **Exemplos completos e rodáveis** — nada de `...` no meio de código que
  deveria funcionar.
- **Admonitions** (`!!! tip`, `!!! warning`, `!!! danger`...) para camadas de
  informação sem quebrar o fluxo.
- Cada página de **Referência** abre com uma analogia simples
  ("pensa como criança 🧒"), depois **Caso de uso**, depois **Possibilidades**,
  e termina com um **Recap**.

### Bilíngue: PT-BR + EN-US

Toda página existe em dois idiomas via
[mkdocs-static-i18n](https://ultrabug.github.io/mkdocs-static-i18n/):

- `pagina.md` → português (padrão).
- `pagina.en.md` → inglês (mesma pasta, sufixo `.en`).

Links internos apontam sempre para o **nome PT** (`pagina.md`) — o i18n resolve
o idioma certo sozinho. Não escreva `.en` nos links.

### Adicionar uma página nova (checklist)

1. Crie `docs/<secao>/<pagina>.md` (PT) seguindo o formato acima.
2. Crie `docs/<secao>/<pagina>.en.md` (EN).
3. Adicione ao `nav:` no `mkdocs.yml`.
4. Adicione a tradução do título em `nav_translations:` (bloco do idioma `en`).
5. `make docs-build` — precisa sair **limpo**.

## Padrões de código (`example/`)

O projeto de exemplo é material didático — o código é lido por quem aprende.
Então:

- **Tipagem** em tudo (parâmetros, retornos, atributos).
- **Docstrings** Google-style em inglês nas classes/métodos.
- **Aspas duplas**, imports absolutos.
- **Views baseadas em classe** por padrão.
- Rode `make test` — a suíte precisa passar.

## Commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

```text
docs: add reference page on signals
feat(example): add tag filtering to the post list
fix(example): stamp published_at only once
test(example): cover comment moderation
```

Prefixos: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`.

## Recap

- `uv sync --all-groups`, depois `make run` / `make test` / `make docs-serve`.
- Docs no estilo tiangolo, bilíngue (`.md` + `.en.md`), links sem `.en`.
- `make docs-build` **estrito** antes de todo PR.
- Código tipado, CBV, testado; commits convencionais.
