# Paginação

Uma lista com 3 posts cabe numa tela. Com 3.000, não. **Paginação** é quebrar uma
lista grande em páginas — melhor para o usuário e para o banco (você busca só um
pedaço de cada vez).

!!! quote "A ideia"
    Pensa num livro: em vez de uma folha gigante enrolada, o conteúdo vem em
    páginas numeradas. Você lê a página 1, vira para a 2. A paginação faz isso
    com a sua lista de posts.

## O jeito fácil: `paginate_by` na `ListView`

Nossa `PostListView` já pagina — bastou **uma linha**:

```python
class PostListView(ListView):
    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 5          # (1)!
```

1. Cinco posts por página. A `ListView` cuida do resto: lê o parâmetro `?page=`
    da URL, fatia o queryset e expõe os objetos de navegação no template.

Com isso, a view coloca no contexto:

| Variável | O que é |
| --- | --- |
| `page_obj` | A página atual (com os itens e a navegação) |
| `paginator` | O paginador (total de páginas/itens) |
| `is_paginated` | `True` se há mais de uma página |
| `posts` | Os itens **desta** página (pelo `context_object_name`) |

## Navegando no template

```django
{% for post in posts %}
  <h2>{{ post.title }}</h2>
{% endfor %}

{% if is_paginated %}
  <nav>
    {% if page_obj.has_previous %}
      <a href="?page={{ page_obj.previous_page_number }}">← Anteriores</a>
    {% endif %}

    <span>Página {{ page_obj.number }} de {{ page_obj.paginator.num_pages }}</span>

    {% if page_obj.has_next %}
      <a href="?page={{ page_obj.next_page_number }}">Próximos →</a>
    {% endif %}
  </nav>
{% endif %}
```

| Atributo de `page_obj` | Vale |
| --- | --- |
| `.number` | Número da página atual |
| `.has_next` / `.has_previous` | Tem próxima/anterior? |
| `.next_page_number` / `.previous_page_number` | Números vizinhos |
| `.paginator.num_pages` | Total de páginas |
| `.paginator.count` | Total de itens |
| `.start_index` / `.end_index` | Faixa de itens exibida (ex.: "6–10 de 42") |

!!! warning "Preserve os outros parâmetros da URL"
    Se a lista também filtra por tag (`?tag=django`), os links de página precisam
    **manter** o filtro, senão a página 2 perde o filtro:
    ```django
    <a href="?page={{ page_obj.next_page_number }}{% if active_tag %}&tag={{ active_tag }}{% endif %}">
    ```

## Como funciona por baixo: `Paginator`

Pensa como criança: o `Paginator` é quem corta o bolo em fatias iguais. A
`ListView` usa ele por você, mas dá para usar direto:

```python
from django.core.paginator import Paginator

posts = Post.objects.published()
paginator = Paginator(posts, 5)         # 5 por página

page = paginator.get_page(2)            # a página 2 (robusto)
page.object_list                        # os 5 itens
page.has_next()                         # True/False
```

!!! tip "`get_page` × `page`"
    - **`get_page(n)`** é à prova de erro: número inválido ou fora do intervalo
      cai numa página válida (1 ou a última). Prefira sempre.
    - **`page(n)`** levanta exceção (`EmptyPage`, `PageNotAnInteger`) para valores
      ruins — você teria que tratar na mão.

## Eficiência

!!! info "Paginação já é eficiente"
    O queryset é preguiçoso: `paginate_by = 5` faz o Django buscar **só** os 5
    itens da página (via `LIMIT/OFFSET`), mais um `COUNT` para saber o total.
    Não traz a lista inteira para a memória.

!!! danger "OFFSET grande é lento"
    Para bases enormes, `?page=100000` usa `OFFSET` gigante e fica lento (o banco
    pula muitas linhas). Para escala extrema, existe a *keyset pagination*
    (paginar por um cursor, ex.: `created_at < X`). Para um blog, o `Paginator`
    padrão é perfeito.

## Recapitulando

- `paginate_by = N` na `ListView` liga a paginação de graça.
- No template: `page_obj` (`.number`, `.has_next`...), `paginator.num_pages`,
  `is_paginated`. **Preserve** os filtros nos links de página.
- Por baixo é o `Paginator`; use `get_page(n)` (robusto), não `page(n)`.
- É eficiente por padrão (`LIMIT/OFFSET` + `COUNT`); só `OFFSET` gigante dói.

Depois de agir (criar, comentar), é bom avisar o usuário. Entram as
**[mensagens](messages.md)**.
