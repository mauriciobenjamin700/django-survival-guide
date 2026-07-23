# Como este projeto foi feito

Uma olhada nos bastidores: as decisões por trás do guia e do projeto de exemplo.
Se você quer montar sua própria documentação nesse estilo, aqui está o mapa.

## A filosofia

Três princípios guiaram cada escolha:

1. **Tipagem clara** — todo o código de exemplo é tipado, para o leitor entender
   a intenção sem adivinhar.
2. **Orientação a objetos** — views baseadas em classe e mixins, composição em
   vez de `if/else`.
3. **Zero mágica** — cada convenção do Django é explicada; nada de "confie que
   funciona".

E um quarto, sobre a escrita: **explicar como para uma criança primeiro**, com
uma analogia concreta, e só então mergulhar no detalhe técnico.

## As peças

| Peça | Escolha | Por quê |
| --- | --- | --- |
| Gerência de deps | [uv](https://docs.astral.sh/uv/) | Rápido, reprodutível (`uv.lock`), baixa o próprio Python |
| Framework | Django 6.0 | Última série estável; o guia mira Python 3.14 |
| API | Django REST Framework | Espelha os conceitos web na camada de API |
| Docs | [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) | Padrão de fato para docs de projetos Python |
| Bilíngue | [mkdocs-static-i18n](https://ultrabug.github.io/mkdocs-static-i18n/) | PT-BR padrão + EN por sufixo `.en.md` |
| API auto | [mkdocstrings](https://mkdocstrings.github.io/) | Docstrings do `example/` viram referência |
| Testes | pytest + pytest-django | Conciso, com fixtures poderosas |
| Deploy | Docker Compose + Gunicorn + WhiteNoise | Sobe app + Postgres com um comando |

## A estrutura em duas partes

O repositório separa **o guia** do **código que ele ensina**:

```text
django-survival-guide/
├── docs/            # o guia (MkDocs, bilíngue)
│   ├── tutorial/    # aprender na ordem
│   └── referencia/  # consultar por tópico
├── example/         # o blog Django rodável
│   ├── config/
│   └── apps/blog/
├── Dockerfile
├── docker-compose.yml
└── mkdocs.yml
```

!!! info "Tutorial × Referência"
    O **Tutorial** é linear: constrói o blog do zero, um conceito por página. A
    **Referência** é um dicionário: cada tópico esgotado em uma página, no
    formato *caso de uso → possibilidades*. Um ensina o caminho; o outro responde
    "e essa opção, o que faz?".

## O código sempre roda

Nada de trechos soltos. Todo exemplo grande vive em `example/`, que:

- passa em `python manage.py check`;
- tem migrações versionadas;
- tem uma suíte `pytest` verde;
- sobe de verdade via `docker compose up`.

A página [Referência de API](../referencia/api.md) é gerada **das docstrings**
desse código — então a documentação nunca descola do que roda.

## O fluxo bilíngue

Cada página é escrita primeiro em **PT-BR** e depois traduzida para **EN-US**,
mantendo o código idêntico e traduzindo só a prosa (e comentários/strings de
exemplo). O build final roda `mkdocs build --strict`: se algo não resolve nos
dois idiomas, ele falha — a documentação não sobe quebrada.

## Recap

- Guia e código separados: `docs/` ensina, `example/` prova.
- Ferramentas modernas: uv, Django 6, MkDocs Material + i18n + mkdocstrings.
- Filosofia: tipagem clara, OO, zero mágica, e explicar como para uma criança.
- Tudo roda e é verificado (`check`, `pytest`, `--strict`, `docker compose`).
