# Referência: cache

!!! quote "Pensa como criança 🧒"
    Toda vez que alguém pergunta "quanto é 7×8?", você pode recalcular... ou
    lembrar que já respondeu 56 há pouco e falar na hora. O **cache** é essa
    memória de respostas prontas: você guarda o resultado caro numa gavetinha
    rápida e, na próxima vez, pega de lá em vez de refazer a conta (ou a query).

## Caso de uso

Uma página de "posts mais populares" faz uma query pesada. Ela quase não muda —
não faz sentido recalcular a cada visita. Você guarda o resultado por 5 minutos:

```python
from django.core.cache import cache

def get_popular_posts() -> list[Post]:
    """Return popular posts, cached for 5 minutes."""
    posts = cache.get("popular_posts")            # (1)!
    if posts is None:                              # (2)!
        posts = list(Post.objects.popular()[:10])
        cache.set("popular_posts", posts, timeout=300)
    return posts
```

1. Tenta pegar da gavetinha.
2. Se não tinha (ou expirou), calcula e guarda. Esse padrão é o
    *cache-aside* — o mais comum.

## Possibilidades

### Configurar o backend: `CACHES`

| Backend | Onde guarda | Bom para |
| --- | --- | --- |
| `LocMemCache` (padrão) | Memória do processo | Dev, testes |
| `RedisCache` | Redis | Produção (compartilhado entre processos) |
| `DatabaseCache` | Tabela no banco | Sem Redis disponível |
| `FileBasedCache` | Arquivos em disco | Casos simples |
| `DummyCache` | Não guarda nada | Desligar cache em dev |

```python
# produção com Redis
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379",
    }
}
```

!!! warning "`LocMemCache` não é compartilhado"
    Ele vive na memória de **um** processo. Com vários workers (Gunicorn), cada
    um tem seu cache — o que confunde. Em produção com múltiplos processos, use
    Redis.

### API de baixo nível (a mais útil)

Pensa como criança: a gavetinha tem só quatro gestos — pôr, pegar, tirar,
"pega ou calcula".

| Método | O que faz |
| --- | --- |
| `cache.set(chave, valor, timeout)` | Guarda (timeout em segundos; `None` = pra sempre) |
| `cache.get(chave, default)` | Pega (ou o padrão) |
| `cache.add(chave, valor)` | Guarda só se ainda não existir |
| `cache.get_or_set(chave, callable, timeout)` | Pega; se faltar, chama e guarda |
| `cache.delete(chave)` | Tira |
| `cache.incr/decr(chave)` | Soma/subtrai (contadores) |
| `cache.set_many / get_many` | Em lote |
| `cache.clear()` | Esvazia tudo |

```python
# get_or_set: o cache-aside em uma linha
posts = cache.get_or_set(
    "popular_posts",
    lambda: list(Post.objects.popular()[:10]),
    timeout=300,
)
```

### Cachear uma view inteira

```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)      # 15 minutos
def home(request): ...
```

Em CBV, decore o `dispatch` com `method_decorator`:

```python
from django.utils.decorators import method_decorator

@method_decorator(cache_page(60 * 15), name="dispatch")
class HomeView(TemplateView): ...
```

### Cachear um pedaço de template

```django
{% load cache %}
{% cache 300 sidebar request.user.id %}
  ... conteúdo caro da sidebar ...
{% endcache %}
```

O `request.user.id` é uma **chave de variação**: cada usuário tem sua versão.

### `cached_property`: cache dentro de um objeto

Pensa como criança: calcula uma vez por objeto e guarda no próprio objeto.

```python
from django.utils.functional import cached_property

class Post(models.Model):
    @cached_property
    def comment_count(self) -> int:
        """Count comments once per instance."""
        return self.comments.count()
```

Acessar `post.comment_count` várias vezes faz a query **uma** vez só.

!!! danger "Invalidar cache é o problema difícil"
    Guardar é fácil; saber **quando jogar fora** é que dói. Estratégias:

    - **Timeout** curto (mais simples): aceita dados um pouco velhos.
    - **Invalidação por chave**: no `post_save`, `cache.delete("popular_posts")`.
    - **Chave versionada**: inclua algo que muda (ex.: `updated_at`) na chave.

    Comece com timeout. Só complique quando "dados velhos por N minutos" não for
    aceitável.

## Recap

- Cache guarda resultados caros numa gavetinha rápida (padrão *cache-aside*:
  `get` → se `None`, calcula e `set`).
- `CACHES` escolhe o backend; use **Redis** em produção (compartilhado),
  `LocMemCache` só em dev.
- Baixo nível: `set`/`get`/`add`/`get_or_set`/`delete`/`incr`. `get_or_set` é o
  atalho.
- View inteira: `cache_page` (+`method_decorator` em CBV); pedaço de template:
  `{% cache %}`; por objeto: `cached_property`.
- O difícil é **invalidar**: comece com timeout curto, evolua para invalidação
  por chave no `post_save`.

Cache acelera. Para tarefas fora do ciclo web, você escreve seus próprios
comandos: **[management commands](management-commands.md)**.
