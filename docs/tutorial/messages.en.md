# Messages to the user

After creating a post or submitting a comment, the user deserves feedback: "it
worked!". Django's **messages** framework does that — little notes that appear
**once** on the next page and then vanish.

!!! quote "The idea"
    Think of a little note stuck on the fridge: "the cake is ready!". You read it
    once and throw it away. Messages work like that — Django keeps the note until
    the next screen, shows it, and discards it. Perfect after a redirect.

## It comes turned on

`startproject` already configures everything: the `django.contrib.messages` app,
the `MessageMiddleware`, and the context processor that exposes `messages` in the
templates. You just use it.

## Adding a message in a view

```python
from django.contrib import messages
from django.http import HttpResponse


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "blog/post_form.html"

    def form_valid(self, form: PostForm) -> HttpResponse:
        """Publish the post and flash a success message."""
        form.instance.author = self.request.user.author_profile
        response = super().form_valid(form)
        messages.success(self.request, f"Post “{self.object.title}” created!")
        return response
```

| Function | Color/tone |
| --- | --- |
| `messages.success(request, text)` | It worked ✅ |
| `messages.info(request, text)` | Information |
| `messages.warning(request, text)` | Attention ⚠️ |
| `messages.error(request, text)` | Error ❌ |
| `messages.debug(request, text)` | Only in development |

## Displaying it in the template

Put this in `base.html`, so it works on every page:

```django
{% if messages %}
  <ul class="messages">
    {% for message in messages %}
      <li class="{{ message.tags }}">{{ message }}</li>
    {% endfor %}
  </ul>
{% endif %}
```

- **`message.tags`** becomes the CSS class (`success`, `error`...) — you style
  each color.
- Iterating `messages` **consumes** the messages: they don't reappear on the next
  page.

!!! info "Why in `base.html`?"
    Since any view can leave a note before redirecting, the place to display it is
    the base layout — that way the message shows up on the destination page,
    whatever it is.

## The shortcut for CBVs: `SuccessMessageMixin`

For the common case (a success message after saving), there's a mixin that saves
you from writing `form_valid`:

```python
from django.contrib.messages.views import SuccessMessageMixin


class PostCreateView(SuccessMessageMixin, LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    success_message = "Post “%(title)s” created successfully!"     # (1)!
```

1. `%(title)s` is replaced by the `title` field of the saved object. The mixin
    adds the message on its own when the form is valid.

!!! tip "A message after a redirect is the right pattern"
    The correct flow after a successful POST is to **redirect** (the
    *POST/Redirect/GET* pattern, which avoids resubmission when you hit F5). The
    flash message survives that redirect and appears on the final page. That's
    exactly what it exists for.

!!! quote "📖 In the official docs"
    - [The messages framework](https://docs.djangoproject.com/en/stable/ref/contrib/messages/)

## Recap

- Messages are flash notes: they appear once after a redirect and then vanish.
- It comes turned on; use `messages.success/info/warning/error(request, text)`.
- Display them in `base.html` by iterating `messages`; `message.tags` gives the
  CSS class.
- In CBVs, `SuccessMessageMixin` + `success_message` (with `%(field)s`) is the
  shortcut.
- It pairs with the POST/Redirect/GET pattern.

You've finished the extended tutorial. To dig deeper into any piece, use the
**[Reference](../referencia/index.md)**.
