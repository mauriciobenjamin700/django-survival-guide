# Roadmap do Django Survival Guide

Roadmap de expansão da documentação, montado a partir de pesquisa web profunda
(docs oficiais do Django 6.0, currículos/livros consagrados — Vincent, Two Scoops,
testdriven.io, roadmap.sh — e o ecossistema real: State of Django 2025, djangopackages,
awesome-django).

**Legenda:** `[6.0]` novidade do Django 6.0 · `[plan]` já estava no backlog ·
`[novo]` descoberto na pesquisa · níveis: 🟢 iniciante · 🟡 intermediário · 🔴 avançado.

> Já cobrimos ~72 páginas (fundamentos web, tutorial, referência, DRF, async,
> bibliotecas, sobre). Este roadmap é só o que **falta**.

---

## P0 — Novidades do Django 6.0 (crítico p/ um guia "2026")

Um guia que se diz de Django 6.0/2026 sem isto nasce desatualizado.

| Tópico | Por quê | Nível |
| --- | --- | --- |
| `[6.0]` **Tasks framework** (background nativo) | Fila de tarefas no core (DEP 14); reposicionar Celery como "quando você cresce" | 🟡 |
| `[6.0]` **Content Security Policy nativa** (`django.middleware.csp`) | Segurança moderna no core (nonces/CSP) | 🟡 |
| `[6.0]` **Template partials** (`{% partialdef %}`/`{% partial %}`) | Componentes reutilizáveis; casa com HTMX | 🟢🟡 |
| `[6.0]` **Composite primary keys** | Chaves compostas no ORM (relações, forms, validação) | 🔴 |

## P1 — Fundamentos ausentes (must-have universal)

Citados por **todas** as fontes; hoje não cobertos ou rasos.

| Tópico | Por quê | Nível |
| --- | --- | --- |
| `[novo]` **Custom user model (cedo!)** | `AbstractUser`/`AbstractBaseUser`; trocar depois é doloroso — todo livro manda fazer antes da 1ª migração | 🟡 |
| `[novo]` **Reset/troca de senha + envio de e-mail** | `PasswordReset*` views, tokens, templates de e-mail; `topics/email` (SMTP/console) | 🟢🟡 |
| `[novo]` **Segurança a fundo** | `SecurityMiddleware`, HTTPS/HSTS/SSL redirect, clickjacking, `django.core.signing`, password hashers (Argon2), `check --deploy` | 🟡🔴 |
| `[plan]` **Permissões detalhadas** + `[novo]` object-level | model/custom perms, grupos, `{% if perms %}`, mixins/decorators + **django-guardian**/**django-rules** (linha) | 🟡 |
| `[novo]` **Config/12-factor** | env vars/secrets fora do VCS, split settings (base/dev/prod), estrutura de projeto p/ escalar | 🟡 |
| `[novo]` **Logging + error reporting** | `LOGGING` dictConfig, níveis, `AdminEmailHandler`, `@sensitive_variables` | 🟡 |
| `[plan]` **Performance & otimização** | N+1, `select/prefetch_related`, `Prefetch`, `bulk_create/update`, índices, `topics/db/optimization`, debug-toolbar/silk | 🟡 |

## P2 — ORM/dados avançado + apps contrib

| Tópico | Por quê | Nível |
| --- | --- | --- |
| `[novo]` **Herança de modelos** (abstract/multi-table/proxy) + **custom managers** | Base de reuso de modelos | 🟡 |
| `[novo]` **Full-text search (Postgres)** | `SearchVector/Query/Rank`, trigram — padrão antes de Elastic | 🟡🔴 |
| `[novo]` **Multi-DB + routers, raw SQL, data migrations (`RunPython`), fixtures, `GeneratedField`** | Cenários reais de produção/legado | 🟡🔴 |
| `[novo]` **`django.contrib.postgres`** | `ArrayField`, `JSONField` PG, ranges, índices PG | 🔴 |
| `[novo]` **Apps contrib**: sitemaps, syndication (RSS/Atom), humanize, sites, redirects, flatpages | Recursos prontos que quase ninguém ensina | 🟢🟡 |
| `[novo]` **Libs de dados**: model-utils, simple-history/auditlog/reversion, import-export, taggit, mptt/treebeard, money, phonenumber | Staples do dia a dia (State of Django) | 🟡 |

## P3 — API moderna

| Tópico | Por quê | Nível |
| --- | --- | --- |
| `[novo]` **DRF a fundo** | auth (Token/JWT/Session), throttling, versioning, nested serializers/routers (temos DRF básico + simplejwt/spectacular no catálogo) | 🟡🔴 |
| `[novo]` **django-ninja** | Maior alta do State of Django 2025; async-first, Pydantic v2, estilo FastAPI — **casa com seu histórico FastAPI** | 🟡 |
| `[novo]` **GraphQL (Strawberry Django)** | Menção/alternativa (Graphene estagnou) | 🔴 |

## P4 — Frontend / UI

| Tópico | Por quê | Nível |
| --- | --- | --- |
| `[plan]` **UI/estilização** (Bootstrap/Tailwind/**crispy-forms**+crispy-bootstrap5) | Deixar o projeto "bonito" | 🟢🟡 |
| `[plan]` **HTMX/Alpine** + `[6.0]` partials + `[novo]` **django-cotton/components** | Dinamismo sem SPA; componentes | 🟡 |
| `[novo]` **django-tables2** | Tabelas HTML declarativas (casa com django-filter) | 🟡 |
| `[novo]` **django-unfold** (admin 2026, Tailwind) | Tema de admin moderno padrão em 2026 | 🟡 |
| `[novo]` **WYSIWYG** (tinymce/ckeditor-5/summernote) + **django-vite/webpack-loader** | Rich text + bundlers JS | 🟢🟡 |

## P5 — Observabilidade / Ops (hoje inexistente)

| Tópico | Por quê | Nível |
| --- | --- | --- |
| `[novo]` **Sentry** (sentry-sdk) | Error tracking #1 em produção | 🟢🟡 |
| `[novo]` **structlog** | Logging estruturado JSON (padrão moderno) | 🟡 |
| `[novo]` **django-prometheus / OpenTelemetry** | Métricas/traces p/ Grafana; auto-instrumentação | 🟡🔴 |
| `[novo]` **django-health-check** | Probes readiness/liveness (k8s/LB) | 🟡 |
| `[novo]` **django-silk** (profiling) + `[plan]` **feature flags** (waffle) | Perf profiling + rollout gradual | 🟡 |

## P6 — Integrações e recursos

| Tópico | Por quê | Nível |
| --- | --- | --- |
| `[plan]` **Consumir APIs externas** (requests/httpx sync+async) | Integrações; timeouts/retries | 🟡 |
| `[novo]` **Pagamentos/Stripe** (checkout, webhooks) | Capstone comum de e-commerce | 🟡🔴 |
| `[plan]` **Relatórios PDF** (WeasyPrint) + `[novo]` **CSV output** | Geração de arquivos (`howto/outputting-csv`) | 🟡 |
| `[plan]` **Scraping com Selenium** | Coleta de dados; headless | 🟡 |
| `[novo]` **File uploads a fundo + conditional GET/ETag** | Upload handlers, limites; cache condicional | 🟡 |

## P7 — Qualidade e entrega

| Tópico | Por quê | Nível |
| --- | --- | --- |
| `[plan]` **Aprofundar testes** | model_bakery/factory_boy, faker, freezegun, responses; testar DRF/Celery/Channels; cobertura | 🟡 |
| `[plan]` **Playwright E2E** | Validar automações no navegador | 🟡 |
| `[novo]` **pre-commit + CI/CD (ensinar)** | Hooks ruff/mypy; GitHub Actions matrizes (py×django), Dependabot/Renovate | 🟢🟡 |
| `[novo]` **Deploy PaaS** (Fly/Railway/Render) + Granian (menção) + k8s/secrets | Receitas concretas além do Docker genérico | 🟡🔴 |

## P8 — Pedagógico / polimento

| Tópico | Por quê | Nível |
| --- | --- | --- |
| `[novo]` **Capstone "projeto real fim-a-fim"** | Fio condutor que amarra tudo (modelo Vincent) | 🟡 |
| `[plan]` **Aprofundar HTML/CSS/JS** | Base mais rica | 🟢 |
| `[plan]` **Imagens nos exemplos visuais** | Screenshots renderizados (Playwright) com legenda | 🟢 |
| `[plan]` **Padrões do mundo real** | service layer, soft-delete/audit, multi-tenancy | 🔴 |

---

## Ordem sugerida de implementação

1. **P0** (novidades 6.0) — diferencial imediato, mantém o guia atual.
2. **P1** (fundamentos ausentes) — maior valor didático; todo mundo precisa.
3. **P3 django-ninja** + **P5 Sentry/observabilidade** — lacunas modernas de alto impacto.
4. **P2/P4/P6/P7** conforme interesse.
5. **P8 capstone** por último — amarra o guia inteiro.

Cada item vira 1+ página bilíngue (PT+EN), estilo do guia (analogia + caso de uso →
possibilidades + recap + link oficial), com exemplos rodáveis quando fizer sentido.

## Fontes

- Django 6.0 release notes — <https://docs.djangoproject.com/en/6.0/releases/6.0/>
- Django docs (topics/howto/ref) — <https://docs.djangoproject.com/en/6.0/>
- State of Django 2025 (JetBrains) — <https://blog.jetbrains.com/pycharm/2025/10/the-state-of-django-2025/>
- Top packages 2025 (Wagtail) — <https://wagtail.org/blog/the-2025-state-of-djangos-top-packages/>
- Essential 3rd-party packages (LearnDjango) — <https://learndjango.com/tutorials/essential-django-3rd-party-packages>
- roadmap.sh/django — <https://roadmap.sh/django>
- Two Scoops of Django · William S. Vincent (Beginners/APIs/Professionals) · testdriven.io
