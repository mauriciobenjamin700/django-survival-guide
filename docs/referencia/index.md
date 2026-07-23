# Referência

!!! quote "Pensa como criança 🧒"
    O **Tutorial** é a aula: você aprende na ordem, um passo de cada vez. Esta
    **Referência** é o dicionário: você vem aqui quando já sabe o que procura e
    quer o detalhe — "quais opções tem esse campo?", "como funciona o cache?".
    Cada página abre com uma analogia simples, mostra um **caso de uso** e depois
    esgota as **possibilidades**.

!!! tip "Como cada página é organizada"
    - **Pensa como criança** — a ideia em uma analogia do dia a dia.
    - **Caso de uso** — um exemplo mínimo e concreto, pronto para rodar.
    - **Possibilidades** — todas as opções/parâmetros, em tabelas + exemplos.
    - **Recap** — o resumo para fixar.

## Mapa dos tópicos

### 🗃️ Modelos e banco de dados

| Página | O que cobre |
| --- | --- |
| [Models — campos](models-fields.md) | Todos os tipos de field e suas opções |
| [Models — Meta](models-meta.md) | Configuração da tabela (ordering, constraints, abstract...) |
| [Campos customizados](custom-fields.md) | Criar seu próprio tipo de field |
| [Content types e relações genéricas](contenttypes.md) | Apontar para qualquer modelo |
| [QuerySet API](querysets-api.md) | Buscar dados: filtros, lookups, `F`/`Q`, N+1 |
| [ORM avançado (expressions)](orm-expressions.md) | `Case`/`When`, `Subquery`, funções, window |
| [Agregação e group by](aggregation-groupby.md) | `aggregate`/`annotate`, contagens por grupo |
| [Transações](transactions.md) | `atomic`, savepoints, `select_for_update`, `on_commit` |

### 🌐 Camada web (HTTP)

| Página | O que cobre |
| --- | --- |
| [Views baseadas em classe](views-cbv.md) | Atributos, ganchos, ordem de execução |
| [Generic views e mixins](generic-views.md) | `TemplateView`/`RedirectView`/`FormView`, catálogo de mixins |
| [URLs e conversores](urls.md) | `path`, conversores, namespaces, `reverse` |
| [Templates](templates.md) | Tags, filtros, herança, custom tags |
| [Formulários e ModelForm](forms.md) | Validação, widgets, `clean` |
| [Validators e validação](validators.md) | Validators, `clean`, `full_clean` |
| [Formsets](formsets.md) | Vários formulários de uma vez |

### 🔐 Usuários, sessão e estado

| Página | O que cobre |
| --- | --- |
| [Autenticação e permissões](auth.md) | `User`, mixins, grupos, custom user |
| [Sessions e messages](sessions-messages.md) | Estado entre requisições, mensagens flash |
| [Cache](cache.md) | Backends, `cache_page`, invalidação |

### ⚙️ Infraestrutura e operação

| Página | O que cobre |
| --- | --- |
| [Settings](settings.md) | Configuração, segurança, ambientes |
| [Middleware](middleware.md) | Camadas em volta das requisições |
| [Signals](signals.md) | Reagir a eventos do modelo |
| [Management commands](management-commands.md) | Seus próprios `manage.py <cmd>` |
| [Arquivos estáticos e media](static-media.md) | CSS/JS × uploads |
| [Storages (armazenamento)](storages.md) | Onde os arquivos moram (disco, S3) |
| [i18n e traduções](i18n.md) | Site em vários idiomas |
| [Deploy](deploy.md) | Pôr no ar com segurança |
| [Deploy com Docker Compose](deploy-docker.md) | Contêineres: app + Postgres |

### 🧪 Qualidade e API

| Página | O que cobre |
| --- | --- |
| [Testes a fundo](testing.md) | pytest, fixtures, clientes, mocking |
| [DRF — serializers e viewsets](drf.md) | API REST sobre os mesmos modelos |
| [Referência de API (código)](api.md) | Doc automática das docstrings do exemplo |

!!! info "Novo no Django?"
    Comece pelo [Tutorial](../tutorial/project-setup.md), que constrói o blog de
    exemplo do zero. Volte para cá quando quiser aprofundar um tópico específico.
