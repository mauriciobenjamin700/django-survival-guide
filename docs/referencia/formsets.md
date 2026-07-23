# Referência: formsets

!!! quote "Pensa como criança 🧒"
    Um formulário é **uma** folha para preencher. Um **formset** é um bloquinho
    com **várias** folhas iguais — para cadastrar 5 telefones de uma vez, ou
    editar todos os itens de um pedido na mesma tela. O Django cuida de contar
    quantas folhas tem, validar todas juntas e ainda deixar você adicionar ou
    apagar folhas.

## Caso de uso

Você quer editar **vários** comentários de um post na mesma página. Em vez de um
form por comentário, um formset agrupa todos:

```python
from django.forms import modelformset_factory

from apps.blog.models import Comment

CommentFormSet = modelformset_factory(
    Comment,
    fields=["author_name", "body", "is_approved"],
    extra=0,            # nº de folhas em branco extras
    can_delete=True,    # permite marcar para apagar
)
```

```python
def edit_comments(request):
    """Edit all comments of a post at once."""
    qs = Comment.objects.filter(post__slug="ola-mundo")
    if request.method == "POST":
        formset = CommentFormSet(request.POST, queryset=qs)
        if formset.is_valid():
            formset.save()
            return redirect("...")
    else:
        formset = CommentFormSet(queryset=qs)
    return render(request, "comments_edit.html", {"formset": formset})
```

## Possibilidades

### As três fábricas

Pensa como criança: cada fábrica monta um bloquinho de folhas diferente.

| Fábrica | Monta um formset de... | Ligado a |
| --- | --- | --- |
| `formset_factory` | `Form` comum (sem modelo) | — |
| `modelformset_factory` | `ModelForm` (vários objetos do modelo) | um modelo |
| `inlineformset_factory` | filhos de um objeto pai | uma relação FK |

### `formset_factory`: formsets sem modelo

```python
from django import forms
from django.forms import formset_factory


class PhoneForm(forms.Form):
    number = forms.CharField(max_length=20)


PhoneFormSet = formset_factory(PhoneForm, extra=3)   # 3 folhas em branco
formset = PhoneFormSet()
```

| Opção da fábrica | O que faz |
| --- | --- |
| `extra` | Quantas folhas em branco a mais mostrar |
| `max_num` | Máximo de folhas |
| `min_num` | Mínimo de folhas |
| `validate_max` / `validate_min` | Valida o máx/mín |
| `can_delete` | Adiciona um checkbox "apagar" em cada folha |
| `can_order` | Permite reordenar as folhas |

### `inlineformset_factory`: filhos de um pai

O mais usado: editar os filhos (Comentários) de um pai (Post) na tela do pai.

```python
from django.forms import inlineformset_factory

CommentInlineFormSet = inlineformset_factory(
    parent_model=Post,
    model=Comment,
    fields=["author_name", "body"],
    extra=1,
    can_delete=True,
)
```

```python
def edit_post_comments(request, slug: str):
    """Edit a post's comments as an inline formset."""
    post = get_object_or_404(Post, slug=slug)
    if request.method == "POST":
        formset = CommentInlineFormSet(request.POST, instance=post)   # (1)!
        if formset.is_valid():
            formset.save()
            return redirect(post.get_absolute_url())
    else:
        formset = CommentInlineFormSet(instance=post)
    return render(request, "edit.html", {"formset": formset})
```

1. `instance=post` amarra o formset ao pai — os filhos salvos já saem com a FK
    apontando para `post`.

### O management form: NÃO esqueça

Pensa como criança: o bloquinho tem uma **capa** que diz quantas folhas existem.
Sem a capa, o Django não sabe processar as folhas e dá erro.

```django
<form method="post">
  {% csrf_token %}
  {{ formset.management_form }}      {# <- a capa, obrigatória! #}
  {% for form in formset %}
    {{ form.as_p }}
    <hr>
  {% endfor %}
  <button type="submit">Salvar todos</button>
</form>
```

!!! danger "`ManagementForm data is missing` = faltou o management form"
    Se você renderizar as folhas mas esquecer `{{ formset.management_form }}`, o
    envio quebra com esse erro. A "capa" guarda `TOTAL_FORMS`/`INITIAL_FORMS` — o
    Django precisa dela para saber quantas folhas processar. Alternativa:
    `{{ formset }}` renderiza a capa junto automaticamente.

### Validação em conjunto

```python
from django.forms import BaseModelFormSet


class BaseCommentFormSet(BaseModelFormSet):
    def clean(self) -> None:
        """Reject duplicate author names across the whole formset."""
        if any(self.errors):
            return
        names = [f.cleaned_data.get("author_name") for f in self.forms]
        if len(names) != len(set(names)):
            raise forms.ValidationError("Nomes de autor duplicados no lote.")


CommentFormSet = modelformset_factory(
    Comment, fields=["author_name", "body"], formset=BaseCommentFormSet,
)
```

- Sobrescreva `clean()` no `BaseModelFormSet` para regras que **cruzam** as
  folhas (ex.: não repetir valores). Passe via `formset=` na fábrica.

### Atributos úteis no template

| Atributo | Vale |
| --- | --- |
| `formset.management_form` | A capa (obrigatória) |
| `formset.forms` | A lista de folhas |
| `formset.total_form_count` | Quantas folhas |
| `formset.empty_form` | Uma folha modelo (para clonar via JS) |
| `formset.non_form_errors` | Erros do `clean()` do formset (não de uma folha) |

!!! quote "📖 Na documentação oficial"
    - [Formsets](https://docs.djangoproject.com/en/stable/topics/forms/formsets/)

## Recap

- Formset = várias folhas do mesmo formulário, validadas e salvas juntas.
- Fábricas: `formset_factory` (sem modelo), `modelformset_factory` (vários
  objetos), `inlineformset_factory` (filhos de um pai, via `instance=`).
- Opções: `extra`, `min_num`/`max_num`, `can_delete`, `can_order`.
- **Sempre** renderize `{{ formset.management_form }}` — sem a "capa", o envio
  quebra.
- Regras que cruzam folhas vão no `clean()` de um `BaseModelFormSet` custom.

Você percorreu a referência do Django de ponta a ponta. 🎉 Volte ao
[Tutorial](../tutorial/project-setup.md) para ver tudo em ação.
