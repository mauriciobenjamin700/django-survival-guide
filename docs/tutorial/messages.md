# Mensagens ao usuário

Depois de criar um post ou enviar um comentário, o usuário merece um retorno:
"deu certo!". O framework de **messages** do Django faz isso — bilhetes que
aparecem **uma vez** na próxima página e somem.

!!! quote "A ideia"
    Pensa num bilhetinho colado na geladeira: "o bolo está pronto!". Você lê uma
    vez e joga fora. As messages são assim — o Django guarda o recado até a
    próxima tela, mostra, e descarta. Perfeito depois de um redirect.

## Já vem ligado

O `startproject` já configura tudo: o app `django.contrib.messages`, o
`MessageMiddleware` e o context processor que expõe `messages` nos templates.
Você só usa.

## Adicionando uma mensagem numa view

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
        messages.success(self.request, f"Post “{self.object.title}” criado!")
        return response
```

| Função | Cor/tom |
| --- | --- |
| `messages.success(request, texto)` | Deu certo ✅ |
| `messages.info(request, texto)` | Informação |
| `messages.warning(request, texto)` | Atenção ⚠️ |
| `messages.error(request, texto)` | Erro ❌ |
| `messages.debug(request, texto)` | Só em desenvolvimento |

## Exibindo no template

Coloque isto no `base.html`, para valer em todas as páginas:

```django
{% if messages %}
  <ul class="messages">
    {% for message in messages %}
      <li class="{{ message.tags }}">{{ message }}</li>
    {% endfor %}
  </ul>
{% endif %}
```

- **`message.tags`** vira a classe CSS (`success`, `error`...) — você estiliza
  cada cor.
- Iterar `messages` **consome** as mensagens: elas não reaparecem na próxima
  página.

!!! info "Por que no `base.html`?"
    Como qualquer view pode deixar um recado antes de redirecionar, o lugar de
    exibir é o layout base — assim a mensagem aparece na página de destino, seja
    ela qual for.

## O atalho para CBVs: `SuccessMessageMixin`

Para o caso comum (mensagem de sucesso após salvar), há um mixin que evita
escrever o `form_valid`:

```python
from django.contrib.messages.views import SuccessMessageMixin


class PostCreateView(SuccessMessageMixin, LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    success_message = "Post “%(title)s” criado com sucesso!"     # (1)!
```

1. `%(title)s` é substituído pelo campo `title` do objeto salvo. O mixin adiciona
    a mensagem sozinho quando o form é válido.

!!! tip "Mensagem depois de redirect é o padrão certo"
    O fluxo correto após um POST bem-sucedido é **redirecionar** (padrão
    *POST/Redirect/GET*, evita reenvio ao dar F5). A mensagem flash sobrevive a
    esse redirect e aparece na página final. É exatamente para isso que ela
    existe.

!!! quote "📖 Na documentação oficial"
    - [The messages framework](https://docs.djangoproject.com/en/stable/ref/contrib/messages/)

## Recapitulando

- Messages são bilhetes flash: aparecem uma vez após um redirect e somem.
- Já vem ligado; use `messages.success/info/warning/error(request, texto)`.
- Exiba no `base.html` iterando `messages`; `message.tags` dá a classe CSS.
- Em CBVs, `SuccessMessageMixin` + `success_message` (com `%(campo)s`) é o
  atalho.
- Combina com o padrão POST/Redirect/GET.

Você concluiu o tutorial estendido. Para aprofundar qualquer peça, use a
**[Referência](../referencia/index.md)**.
