# Referência: sessions e messages

!!! quote "Pensa como criança 🧒"
    O site esquece você a cada clique — cada requisição é uma pessoa nova
    chegando. A **sessão** é uma mochilinha que fica guardada no servidor com uma
    etiqueta; você carrega só a etiqueta (um cookie) e, a cada visita, o servidor
    pega sua mochila de volta. As **messages** são bilhetinhos: você cola um
    ("salvo com sucesso!"), ele aparece **uma vez** na próxima tela e some.

## Caso de uso

### Sessão: lembrar algo entre páginas

```python
def add_to_cart(request: HttpRequest, product_id: int) -> HttpResponse:
    """Store the cart in the session so it survives across requests."""
    cart: list[int] = request.session.get("cart", [])
    cart.append(product_id)
    request.session["cart"] = cart          # (1)!
    return redirect("cart")
```

1. Escrever numa chave marca a sessão como "suja" e o Django a salva sozinho.

### Message: avisar o usuário na próxima tela

```python
from django.contrib import messages

def form_valid(self, form):
    response = super().form_valid(form)
    messages.success(self.request, "Post publicado com sucesso!")
    return response
```

```django
{% for message in messages %}
  <p class="alert {{ message.tags }}">{{ message }}</p>
{% endfor %}
```

## Possibilidades

### Sessões: a API

| Operação | Código |
| --- | --- |
| Ler (com padrão) | `request.session.get("chave", default)` |
| Escrever | `request.session["chave"] = valor` |
| Apagar uma chave | `del request.session["chave"]` |
| Existe? | `"chave" in request.session` |
| Expiração | `request.session.set_expiry(3600)` (segundos; `0` = ao fechar o navegador) |
| Esvaziar tudo | `request.session.flush()` (usa no logout) |

!!! tip "O Django detecta a maioria das mudanças sozinho"
    Atribuir (`session["x"] = ...`) marca como suja e salva. Mas **mutar em
    profundidade** (ex.: `session["cart"].append(x)` sem reatribuir) pode passar
    batido — por isso o exemplo do carrinho reatribui `session["cart"] = cart`.
    Na dúvida, `request.session.modified = True`.

### Onde a mochila fica guardada: `SESSION_ENGINE`

| Backend | Onde guarda | Bom para |
| --- | --- | --- |
| `db` (padrão) | Tabela no banco | Geral |
| `cache` | No cache (ex.: Redis) | Velocidade |
| `cached_db` | Cache + banco | Velocidade + durabilidade |
| `signed_cookies` | No próprio cookie (assinado) | Sem estado no servidor (cuidado com tamanho) |

```python
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_COOKIE_AGE = 1209600   # 2 semanas, em segundos
```

!!! danger "O cookie carrega só a etiqueta, não a mochila"
    Com os backends de servidor, o cookie guarda só o **id** da sessão. Os dados
    ficam no servidor. Com `signed_cookies`, os dados vão no cookie (assinados,
    não criptografados) — nunca ponha segredos ali, e cuidado com o limite de
    ~4KB.

### Messages: níveis e uso

Pensa como criança: cada bilhetinho tem uma cor conforme o tom.

| Função | Nível | Uso típico |
| --- | --- | --- |
| `messages.debug(request, ...)` | DEBUG | Só em desenvolvimento |
| `messages.info(request, ...)` | INFO | Informação neutra |
| `messages.success(request, ...)` | SUCCESS | "Deu certo!" |
| `messages.warning(request, ...)` | WARNING | Atenção |
| `messages.error(request, ...)` | ERROR | Algo falhou |

`{{ message.tags }}` no template vira a classe CSS (`success`, `error`...) para
você estilizar.

!!! info "Mensagem aparece UMA vez e some"
    Messages usam o padrão *flash*: são guardadas (na sessão) até serem
    **exibidas**, e então descartadas. Perfeito para "salvo com sucesso" após um
    redirect — não repete na próxima navegação.

### `SuccessMessageMixin`: o atalho para CBVs

```python
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import CreateView


class PostCreateView(SuccessMessageMixin, CreateView):
    model = Post
    fields = ["title", "body"]
    success_message = "Post “%(title)s” criado!"    # (1)!
```

1. `%(title)s` é preenchido com o campo `title` do objeto salvo.

## Recap

- A **sessão** é a mochila no servidor; o cookie carrega só a etiqueta (id).
  API tipo dict: `get`/`[]=`/`del`/`flush`; `set_expiry` controla validade.
- Reatribua ao mutar estruturas aninhadas (ou `session.modified = True`).
- `SESSION_ENGINE` escolhe onde guardar (db/cache/cached_db/signed_cookies).
- **Messages** são bilhetes flash: `success`/`info`/`warning`/`error`, exibidos
  uma vez e descartados; `{{ message.tags }}` dá a classe CSS.
- Em CBVs, `SuccessMessageMixin` + `success_message` é o atalho.

Guardar estado rápido leva ao próximo tema: **[cache](cache.md)**.
