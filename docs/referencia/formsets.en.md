# Reference: formsets

!!! quote "Think like a child 🧒"
    A form is **one** sheet to fill in. A **formset** is a little pad with
    **several** identical sheets — to register 5 phone numbers at once, or edit all
    the items of an order on the same screen. Django takes care of counting how
    many sheets there are, validating them all together, and even letting you add
    or delete sheets.

## Use case

You want to edit **several** comments of a post on the same page. Instead of one
form per comment, a formset groups them all:

```python
from django.forms import modelformset_factory

from apps.blog.models import Comment

CommentFormSet = modelformset_factory(
    Comment,
    fields=["author_name", "body", "is_approved"],
    extra=0,            # number of extra blank sheets
    can_delete=True,    # allows marking for deletion
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

## Possibilities

### The three factories

Think like a child: each factory builds a different little pad of sheets.

| Factory | Builds a formset of... | Tied to |
| --- | --- | --- |
| `formset_factory` | plain `Form` (no model) | — |
| `modelformset_factory` | `ModelForm` (several model objects) | one model |
| `inlineformset_factory` | children of a parent object | one FK relation |

### `formset_factory`: formsets without a model

```python
from django import forms
from django.forms import formset_factory


class PhoneForm(forms.Form):
    number = forms.CharField(max_length=20)


PhoneFormSet = formset_factory(PhoneForm, extra=3)   # 3 blank sheets
formset = PhoneFormSet()
```

| Factory option | What it does |
| --- | --- |
| `extra` | How many extra blank sheets to show |
| `max_num` | Maximum number of sheets |
| `min_num` | Minimum number of sheets |
| `validate_max` / `validate_min` | Validates the max/min |
| `can_delete` | Adds a "delete" checkbox to each sheet |
| `can_order` | Allows reordering the sheets |

### `inlineformset_factory`: children of a parent

The most used: editing the children (Comments) of a parent (Post) on the parent's
screen.

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

1. `instance=post` ties the formset to the parent — the saved children come out
    with the FK already pointing at `post`.

### The management form: DON'T forget it

Think like a child: the little pad has a **cover** that says how many sheets
there are. Without the cover, Django doesn't know how to process the sheets and
throws an error.

```django
<form method="post">
  {% csrf_token %}
  {{ formset.management_form }}      {# <- the cover, required! #}
  {% for form in formset %}
    {{ form.as_p }}
    <hr>
  {% endfor %}
  <button type="submit">Save all</button>
</form>
```

!!! danger "`ManagementForm data is missing` = the management form is missing"
    If you render the sheets but forget `{{ formset.management_form }}`, the
    submission breaks with that error. The "cover" holds
    `TOTAL_FORMS`/`INITIAL_FORMS` — Django needs it to know how many sheets to
    process. Alternative: `{{ formset }}` renders the cover along automatically.

### Group validation

```python
from django.forms import BaseModelFormSet


class BaseCommentFormSet(BaseModelFormSet):
    def clean(self) -> None:
        """Reject duplicate author names across the whole formset."""
        if any(self.errors):
            return
        names = [f.cleaned_data.get("author_name") for f in self.forms]
        if len(names) != len(set(names)):
            raise forms.ValidationError("Duplicate author names in the batch.")


CommentFormSet = modelformset_factory(
    Comment, fields=["author_name", "body"], formset=BaseCommentFormSet,
)
```

- Override `clean()` on the `BaseModelFormSet` for rules that **cross** the sheets
  (e.g. not repeating values). Pass it via `formset=` on the factory.

### Useful attributes in the template

| Attribute | Holds |
| --- | --- |
| `formset.management_form` | The cover (required) |
| `formset.forms` | The list of sheets |
| `formset.total_form_count` | How many sheets |
| `formset.empty_form` | A template sheet (to clone via JS) |
| `formset.non_form_errors` | Errors from the formset's `clean()` (not from a single sheet) |

!!! quote "📖 In the official docs"
    - [Formsets](https://docs.djangoproject.com/en/stable/topics/forms/formsets/)

## Recap

- Formset = several sheets of the same form, validated and saved together.
- Factories: `formset_factory` (no model), `modelformset_factory` (several
  objects), `inlineformset_factory` (children of a parent, via `instance=`).
- Options: `extra`, `min_num`/`max_num`, `can_delete`, `can_order`.
- **Always** render `{{ formset.management_form }}` — without the "cover", the
  submission breaks.
- Rules that cross sheets go in the `clean()` of a custom `BaseModelFormSet`.

You've gone through the Django reference from end to end. 🎉 Head back to the
[Tutorial](../tutorial/project-setup.md) to see it all in action.
