# Django Survival Guide 🐍

Bem-vindo(a)! Este é um guia para aprender **Django moderno** do zero — com
**tipagem clara**, **orientação a objetos** e **zero mágica**.

A ideia é simples: em vez de decorar comandos, você vai **entender o que cada
peça faz e por quê**. Cada página constrói um conceito em cima do anterior, com
exemplos completos e prontos para rodar — no estilo da
[documentação do FastAPI](https://fastapi.tiangolo.com).

!!! info "Para quem é este guia"
    - Quem sabe **Python** (funções, classes, type hints) e quer aprender Django.
    - Quem já usou Django "no chute" e quer entender o que acontece por baixo.
    - Quem prefere **views baseadas em classe** e código explícito e tipado.

## O que você vai construir

Um **blog** completo e funcional, evoluindo de forma progressiva:

1. **Django puro** — models, admin, ORM, views baseadas em classe, templates,
   formulários e autenticação.
2. **API REST** — a mesma base de dados exposta como uma API com o
   Django REST Framework (DRF).

```text
Post ──< Comment          (um post tem vários comentários)
Post >── Author           (cada post tem um autor)
Post >──< Tag             (posts e tags: muitos-para-muitos)
```

Todo o código vive na pasta [`example/`](https://github.com/mauriciobenjamin700/django-survival-guide/tree/main/example)
do repositório e **roda de verdade** — nada de trechos soltos.

## Filosofia

!!! quote "Três princípios"
    1. **Tipagem clara.** Toda função, método e atributo é tipado. O editor te
       ajuda, e o leitor entende a intenção sem adivinhar.
    2. **Orientação a objetos.** Preferimos views baseadas em classe e mixins:
       comportamento reaproveitável e composição em vez de `if/else`.
    3. **Zero mágica.** Nada de "confie e funciona". Cada convenção do Django é
       explicada — o que ela faz, quando usar, e o que aconteceria sem ela.

## Versões usadas

| Ferramenta | Versão | Observação |
| --- | --- | --- |
| Python | 3.14 | Alvo do guia; o exemplo roda em 3.13+ |
| Django | 6.0 | Última série estável |
| Django REST Framework | 3.17 | Camada de API (guia avançado) |
| uv | 0.7+ | Gerenciador de dependências e Python |

!!! tip "Como aproveitar melhor"
    Leia na ordem do menu à esquerda. Cada página termina com um **Recapitulando**
    curto. Rode o código conforme avança — aprender Django é aprender fazendo. 🚀

Pronto? Comece pela **[Instalação](get-started/installation.md)**.
