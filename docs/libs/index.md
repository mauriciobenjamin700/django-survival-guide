# Bibliotecas do ecossistema

O Django faz muito sozinho, mas a comunidade construiu bibliotecas que resolvem
problemas comuns sem você reinventar a roda: login social, tarefas em segundo
plano, tempo real, filtros de API. Esta seção cobre as mais usadas.

!!! quote "Pensa como criança 🧒"
    O Django é uma caixa de Lego enorme. As bibliotecas são **peças especiais**
    prontas — uma roda que já gira, uma porta que já abre. Você encaixa em vez de
    esculpir do zero. Mas cada peça a mais é uma peça a mais para **manter** —
    então escolha com cuidado.

## O mapa desta seção

| Biblioteca | Resolve |
| --- | --- |
| [django-allauth](allauth.md) | Cadastro, login (inclusive social), verificação de e-mail |
| [Celery](celery.md) | Tarefas em segundo plano e agendadas (fora do request) |
| [Django Channels](channels.md) | WebSockets e tempo real (chat, notificações) |
| [SSE — Server-Sent Events](sse.md) | Tempo real de uma via (servidor → cliente) |
| [Web Push](webpush.md) | Notificações mesmo com o site fechado |
| [django-filter](django-filter.md) | Filtrar listagens e APIs por query params |
| [Afins (catálogo)](afins.md) | debug-toolbar, extensions, environ, CORS, JWT, OpenAPI... |
| [Serviços em contêiner](containers.md) | Postgres, Redis, RabbitMQ, MinIO, Flower via compose |

## Como escolher (e adicionar) uma biblioteca

Antes de instalar qualquer coisa, pergunte:

1. **O Django já faz isso?** Muita gente instala lib para o que já existe nativo
   (auth, cache, sessions). Cheque a [Referência](../referencia/index.md) primeiro.
2. **A lib é mantida?** Veja no GitHub: commits recentes, issues respondidas,
   compatibilidade com a sua versão do Django. Uma lib abandonada vira dívida.
3. **Vale o custo?** Cada dependência é mais superfície para atualizar, quebrar e
   auditar. Bibliotecas grandes (Celery, Channels) mudam a arquitetura do projeto.

!!! tip "O ritual de adicionar uma lib Django"
    A maioria segue o mesmo passo a passo:
    ```bash
    uv add nome-da-lib
    ```
    ```python
    # settings.py
    INSTALLED_APPS = [
        # ...
        "a_lib",            # (1) registra o app
    ]
    ```
    ```python
    # urls.py (se a lib expõe rotas)
    path("prefixo/", include("a_lib.urls")),
    ```
    ```bash
    python manage.py migrate   # (2) se a lib tem models
    ```
    Instalar → registrar em `INSTALLED_APPS` → (rotas) → `migrate`. Guarde esse
    ritmo; ele se repete em quase toda página desta seção.

!!! warning "Fixe versões e leia o changelog ao atualizar"
    O `uv.lock` já fixa as versões. Ao subir uma lib de versão maior (ex.: Celery
    5→6), **leia o changelog** — libs de infraestrutura quebram compatibilidade
    entre versões maiores com frequência.

## Recapitulando

- Bibliotecas encaixam soluções prontas; cada uma é também manutenção.
- Antes de instalar: o Django já faz? a lib é mantida? o custo compensa?
- O ritual: `uv add` → `INSTALLED_APPS` → rotas (se houver) → `migrate`.
- Fixe versões (`uv.lock`) e leia changelogs em upgrades maiores.

Comece pela que quase todo projeto precisa: autenticação turbinada com
**[django-allauth](allauth.md)**.
