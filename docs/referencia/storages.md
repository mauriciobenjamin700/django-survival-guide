# Referência: storages (armazenamento de arquivos)

!!! quote "Pensa como criança 🧒"
    Quando alguém envia uma foto, ela precisa morar em algum lugar. Um **storage**
    é o "armário" onde os arquivos ficam. Pode ser uma gaveta no seu computador
    (disco local) ou um galpão gigante na nuvem (S3). O truque do Django: seu
    código fala com um armário **abstrato** — trocar de armário não muda o código.

## Caso de uso

Em desenvolvimento os uploads ficam no disco; em produção, na Amazon S3. Você não
muda o modelo — só o **storage** configurado:

```python
# o modelo é sempre o mesmo
class Profile(models.Model):
    avatar = models.ImageField(upload_to="avatars/")
```

```python
# settings.py — dev: disco local
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# settings.py — produção: S3 (via django-storages)
STORAGES = {
    "default": {"BACKEND": "storages.backends.s3.S3Storage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
```

`profile.avatar.url` funciona igual nos dois — muda só para onde aponta.

## Possibilidades

### O setting `STORAGES`

Pensa como criança: dois armários com apelidos fixos.

| Apelido | Guarda |
| --- | --- |
| `default` | Uploads dos usuários (o que `FileField`/`ImageField` gravam) |
| `staticfiles` | Arquivos estáticos (CSS/JS), destino do `collectstatic` |

```python
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": "/data/media", "base_url": "/media/"},
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
```

### Backends comuns

| Backend | Armário |
| --- | --- |
| `FileSystemStorage` | Disco local |
| `whitenoise...CompressedManifestStaticFilesStorage` | Disco, comprimido + hash no nome |
| `storages.backends.s3.S3Storage` | Amazon S3 / compatível (MinIO, R2) |
| `storages.backends.gcloud.GoogleCloudStorage` | Google Cloud Storage |
| `storages.backends.azure_storage.AzureStorage` | Azure Blob |

Os de nuvem vêm do pacote [django-storages](https://django-storages.readthedocs.io/):

```bash
uv add "django-storages[s3]"
```

### A API de um storage

Todo storage — local ou nuvem — expõe a mesma interface. É por isso que trocar o
backend não quebra seu código:

| Método/atributo | Faz |
| --- | --- |
| `storage.save(name, content)` | Grava um arquivo, retorna o nome final |
| `storage.open(name)` | Abre para leitura |
| `storage.delete(name)` | Apaga |
| `storage.exists(name)` | Existe? |
| `storage.url(name)` | URL pública |
| `storage.size(name)` | Tamanho em bytes |

```python
from django.core.files.base import ContentFile
from django.core.files.storage import storages

default = storages["default"]
name = default.save("relatorios/x.txt", ContentFile(b"conteudo"))
url = default.url(name)
```

### `upload_to`: onde dentro do armário

```python
def by_user(instance, filename: str) -> str:
    """Store each user's uploads under their own folder."""
    return f"users/{instance.user_id}/{filename}"


class Profile(models.Model):
    avatar = models.ImageField(upload_to=by_user)     # ou upload_to="avatars/%Y/%m/"
```

- **String** com `strftime` (`"avatars/%Y/%m/"`) → subpasta por data.
- **Callable** `(instance, filename) -> str` → controle total do caminho.

### Storage por campo

Um campo pode usar um armário diferente do `default`:

```python
from storages.backends.s3 import S3Storage

private_store = S3Storage(bucket_name="privados", default_acl="private")


class Invoice(models.Model):
    pdf = models.FileField(storage=private_store)
```

!!! tip "Arquivos privados: sirva por URL assinada"
    Uploads sensíveis (notas fiscais, documentos) não devem ficar públicos. Em
    storages de nuvem, use ACL privada e gere **URLs assinadas** (temporárias)
    para o download — o `django-storages` faz isso via `querystring_auth`.

### Boas práticas

!!! danger "Em produção, o Django NÃO serve os arquivos"
    Em produção, uploads são servidos pelo storage de nuvem (S3) ou pelo servidor
    web (Nginx) — nunca pelo processo Django, que é lento e inseguro para isso. O
    truque de servir media pelo `runserver` (ver [static-media](static-media.md))
    é só para desenvolvimento.

!!! tip "Nunca confie no nome do arquivo enviado"
    O storage já sanitiza e, se houver colisão, acrescenta um sufixo aleatório.
    Não use o nome cru do upload em caminhos sem passar pelo `upload_to`.

!!! quote "📖 Na documentação oficial"
    - [File storage API](https://docs.djangoproject.com/en/stable/ref/files/storage/)
    - [django-storages](https://django-storages.readthedocs.io/)

## Recap

- Um storage é o "armário" dos arquivos; o código fala com uma interface
  **abstrata**, então trocar disco↔nuvem não muda os modelos.
- `STORAGES` define `default` (uploads) e `staticfiles`; backends: local,
  WhiteNoise, S3/GCS/Azure (via django-storages).
- API comum: `save`/`open`/`delete`/`url`/`exists`. `upload_to` (string com data
  ou callable) decide o caminho; `storage=` troca o armário por campo.
- Arquivos privados → ACL privada + URL assinada. Em produção, quem serve é
  nuvem/Nginx, não o Django.

Você percorreu a referência do Django de ponta a ponta. 🎉 Volte ao
[mapa da referência](index.md) ou ao [tutorial](../tutorial/project-setup.md).
