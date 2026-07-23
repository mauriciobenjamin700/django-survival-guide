# Referência: arquivos estáticos e media

!!! quote "Pensa como criança 🧒"
    Tem dois tipos de coisa que não são "texto do banco". Os **estáticos** são os
    brinquedos que já vêm na caixa do jogo (o CSS, o JavaScript, o logo) — você
    põe e eles não mudam. Os **media** são os desenhos que **as crianças fazem**
    enquanto brincam (fotos de perfil, anexos) — aparecem depois, durante o uso.
    Django trata os dois de jeitos diferentes.

## Caso de uso

### Estático: um CSS do seu app

```text
apps/blog/static/blog/style.css
```

```django
{% load static %}
<link rel="stylesheet" href="{% static 'blog/style.css' %}">
```

### Media: um avatar enviado pelo usuário

```python
class Profile(models.Model):
    avatar = models.ImageField(upload_to="avatars/%Y/%m/", blank=True)
```

```django
{% if profile.avatar %}
  <img src="{{ profile.avatar.url }}" alt="avatar">
{% endif %}
```

## Possibilidades

### Estático × media: a diferença que confunde todo mundo

| | Estático | Media |
| --- | --- | --- |
| O que é | CSS, JS, imagens do tema | Uploads dos usuários |
| Quem cria | Você (dev) | Os usuários (runtime) |
| Setting de URL | `STATIC_URL` | `MEDIA_URL` |
| Setting de pasta | `STATIC_ROOT` (destino do collectstatic) | `MEDIA_ROOT` |
| Comando | `collectstatic` | — |
| Field no modelo | — | `FileField` / `ImageField` |

!!! danger "Nunca aponte os dois para a mesma pasta"
    Misturar estático e media é pedir problema: o `collectstatic` pode sobrescrever
    ou apagar uploads. São mundos separados — pastas separadas.

### Estáticos: onde o Django procura

Pensa como criança: o Django tem uma lista de caixas onde procurar brinquedos.

| Setting | Papel |
| --- | --- |
| `STATIC_URL` | Prefixo das URLs (`static/`) |
| `STATICFILES_DIRS` | Pastas **extras** de estáticos do projeto (fora dos apps) |
| `STATIC_ROOT` | Pasta única onde `collectstatic` **junta** tudo (produção) |

```python
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "assets"]     # estáticos do projeto (opcional)
STATIC_ROOT = BASE_DIR / "staticfiles"        # destino do collectstatic
```

- **`app/static/app/...`** → estáticos de cada app (achados automaticamente).
- **`{% static 'caminho' %}`** → gera a URL certa, nunca escreva à mão.

### `collectstatic`: juntar para produção

Pensa como criança: antes de sair de casa, você junta todos os brinquedos
espalhados numa mochila só (`STATIC_ROOT`), para o entregador levar de uma vez.

```bash
python manage.py collectstatic --no-input
```

Em desenvolvimento (`DEBUG=True`), o `runserver` serve os estáticos direto — você
**não** precisa rodar `collectstatic`. Ele é para produção.

### `STORAGES`: como e onde guardar (Django atual)

O setting `STORAGES` define o backend de armazenamento de `default` (media) e
`staticfiles`:

```python
STORAGES = {
    "default": {                                    # uploads (media)
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {                                # estáticos
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
```

| Backend comum | Guarda em |
| --- | --- |
| `FileSystemStorage` | Disco local |
| `whitenoise...CompressedManifestStaticFilesStorage` | Disco, comprimido + hash no nome (cache eterno) |
| `storages.backends.s3.S3Storage` (django-storages) | Amazon S3 / compatível |

!!! tip "Hash no nome = cache eterno seguro"
    O storage com *manifest* renomeia `style.css` para `style.a1b2c3.css`. Como o
    nome muda quando o conteúdo muda, o navegador pode cachear "para sempre" sem
    servir versão velha. O `{% static %}` resolve o nome com hash sozinho.

### Servindo media em desenvolvimento

Em `DEBUG=True`, adicione ao `urls.py` raiz para o `runserver` servir uploads:

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... suas rotas ...
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

!!! danger "Em produção, media NÃO é servida pelo Django"
    Em produção, quem serve arquivos é o servidor web (Nginx) ou um storage de
    nuvem (S3). Deixar o Django servir uploads em produção é lento e inseguro. O
    truque acima é **só** para desenvolvimento.

### O `FileField` / `ImageField` na prática

| Opção | O que faz |
| --- | --- |
| `upload_to` | Subpasta dentro do `MEDIA_ROOT` (aceita `%Y/%m/` ou um callable) |
| `storage` | Backend específico para esse campo |
| `.url` | URL pública do arquivo |
| `.path` | Caminho no disco (só storages locais) |

```python
def user_directory(instance: "Profile", filename: str) -> str:
    """Store each user's uploads under their own folder."""
    return f"users/{instance.user_id}/{filename}"


class Profile(models.Model):
    avatar = models.ImageField(upload_to=user_directory, blank=True)
```

!!! info "`ImageField` precisa do Pillow"
    `ImageField` valida que o arquivo é uma imagem — para isso, instale o
    `Pillow` (`uv add pillow`). `FileField` aceita qualquer arquivo, sem Pillow.

!!! quote "📖 Na documentação oficial"
    - [How to manage static files](https://docs.djangoproject.com/en/stable/howto/static-files/)
    - [Managing files](https://docs.djangoproject.com/en/stable/topics/files/)

## Recap

- **Estático** (vem com o projeto) × **media** (upload do usuário) — pastas e
  settings separados, nunca misturados.
- Estáticos: `{% static %}` gera a URL; `STATICFILES_DIRS` (extras),
  `STATIC_ROOT` (destino do `collectstatic`, só produção).
- `STORAGES` define os backends; storage com hash no nome permite cache eterno.
- Media em dev: sirva via `static()` no `urls.py` sob `if settings.DEBUG`; em
  produção, Nginx/S3.
- `FileField`/`ImageField`: `upload_to` (string ou callable), `.url`/`.path`;
  `ImageField` exige Pillow.

Arquivos resolvidos. Agora deixar o site falar vários idiomas: **[i18n](i18n.md)**.
