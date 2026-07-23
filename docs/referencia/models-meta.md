# Referência: a classe `Meta` do modelo

!!! quote "Pensa como criança 🧒"
    Se o modelo é uma **caixa de brinquedos** e os fields são as gavetas, a
    `class Meta` é a **etiqueta na tampa da caixa**. Ela não guarda brinquedo
    nenhum — ela diz *como a caixa se comporta*: qual o nome dela, em que ordem
    os brinquedos aparecem, e regras do tipo "não pode ter dois brinquedos com o
    mesmo nome".

## Caso de uso

Seus posts aparecem fora de ordem, o nome da tabela ficou feio, e você quer
impedir dois posts com o mesmo título do mesmo autor. Nada disso é sobre *um*
campo — é sobre a **tabela inteira**. Esse é o trabalho da `Meta`:

```python
# apps/blog/models.py
from django.db import models


class Post(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey("Author", on_delete=models.CASCADE)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-published_at"]                 # mais novos primeiro
        verbose_name = "post"                          # nome bonito, singular
        verbose_name_plural = "posts"                  # nome bonito, plural
        constraints = [
            models.UniqueConstraint(
                fields=["author", "title"],
                name="unique_title_per_author",
            )
        ]
```

!!! info "A `Meta` é uma classe *dentro* do modelo"
    Ela não herda de nada, não vira tabela, não tem métodos seus. É só um
    "quadro de recados" que o Django lê para configurar o modelo. Toda opção
    abaixo é opcional.

## Possibilidades

### Ordenação e nomes

| Opção | O que faz | Exemplo |
| --- | --- | --- |
| `ordering` | Ordem padrão das consultas | `["-published_at", "title"]` |
| `verbose_name` | Nome singular exibido | `"artigo"` |
| `verbose_name_plural` | Nome plural exibido | `"artigos"` |
| `db_table` | Nome da tabela no banco | `"blog_posts"` |
| `db_table_comment` | Comentário da tabela no banco | `"Posts do blog"` |

!!! tip "O `-` no `ordering` significa decrescente"
    `"-published_at"` = do mais novo para o mais velho. Sem o `-`, é crescente.
    Pensa como criança: o `-` é a setinha "de cima pra baixo".

!!! warning "Sempre defina `verbose_name_plural` em português"
    O Django pluraliza em inglês (adiciona "s"). "categoria" viraria
    "categorias"? Não: viraria "categorias" só por sorte, mas "pessoa" viraria
    "pessoas"? Não, "pessos". Sempre declare o plural você mesmo.

### Restrições e índices

A forma **moderna** (Django atual) de garantir regras no banco:

```python
class Enrollment(models.Model):
    student = models.ForeignKey("Student", on_delete=models.CASCADE)
    course = models.ForeignKey("Course", on_delete=models.CASCADE)
    grade = models.IntegerField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"],
                name="unique_enrollment",
            ),
            models.CheckConstraint(
                condition=models.Q(grade__gte=0) & models.Q(grade__lte=100),
                name="grade_between_0_and_100",
            ),
        ]
        indexes = [
            models.Index(fields=["course", "-grade"], name="course_grade_idx"),
        ]
```

| Opção | O que faz |
| --- | --- |
| `constraints` | Lista de `UniqueConstraint` / `CheckConstraint` aplicadas **no banco** |
| `indexes` | Lista de `Index` para acelerar consultas |
| `unique_together` | Forma **antiga** de unicidade combinada (prefira `UniqueConstraint`) |

!!! danger "Prefira `constraints`/`indexes` — e `index_together` nem existe mais"
    `UniqueConstraint` e `Index` são mais poderosas (aceitam condições,
    expressões, nomes) e são o caminho recomendado hoje.

    - `unique_together` ainda **funciona**, mas está em desuso — prefira
      `UniqueConstraint`.
    - `index_together` foi **removido no Django 5.1** (não existe no 6.0). Use
      `Meta.indexes` com `models.Index(...)`.

!!! info "Constraint × validação de formulário"
    Uma `constraint` vive **no banco** — é a última linha de defesa, garante
    integridade mesmo se alguém inserir dados por fora do Django. A validação de
    formulário é a primeira linha (mensagem amigável). Use as duas: cinto e
    suspensório.

### Modelos abstratos: herança sem tabela

Quer que vários modelos compartilhem os mesmos campos (ex.: `created_at`,
`updated_at`) sem repetir código? Use um modelo **abstrato**:

```python
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True     # (1)!


class Post(TimeStampedModel):      # herda created_at e updated_at
    title = models.CharField(max_length=200)


class Comment(TimeStampedModel):   # também herda
    body = models.TextField()
```

1. `abstract = True` diz: "não crie tabela para *mim*; só empreste meus campos
   para quem herdar." Pensa como criança: é uma **receita de bolo**, não o bolo.
   Cada filho assa o próprio bolo com os mesmos ingredientes.

| Opção | O que faz |
| --- | --- |
| `abstract` | `True` = modelo-receita, sem tabela própria |
| `proxy` | `True` = mesma tabela do pai, só muda comportamento (métodos, ordering) |
| `managed` | `False` = o Django não cria/apaga a tabela (banco legado) |

!!! tip "Onde a `Meta` do filho herda da `Meta` do pai"
    Ao herdar de um abstrato, o filho **herda a `Meta`** do pai. Se o filho
    precisa de opções próprias mas quer manter as do pai, herde explicitamente:
    ```python
    class Post(TimeStampedModel):
        class Meta(TimeStampedModel.Meta):
            ordering = ["-created_at"]
    ```

### Permissões

```python
class Report(models.Model):
    class Meta:
        permissions = [
            ("can_export", "Pode exportar relatórios"),
            ("can_publish", "Pode publicar relatórios"),
        ]
        default_permissions = ["add", "change", "delete", "view"]  # o padrão
```

| Opção | O que faz |
| --- | --- |
| `permissions` | Permissões **extras** além das quatro automáticas |
| `default_permissions` | Personaliza as automáticas (`add`/`change`/`delete`/`view`) |

### Tabela-resumo de todas as opções úteis

| Opção | Categoria |
| --- | --- |
| `ordering` | Ordenação |
| `verbose_name`, `verbose_name_plural` | Nomes exibidos |
| `db_table`, `db_table_comment` | Nome/comentário da tabela |
| `constraints` | Restrições no banco |
| `indexes` | Índices |
| `unique_together` | (legado — prefira `UniqueConstraint`; `index_together` foi removido no 5.1) |
| `abstract` | Modelo-receita sem tabela |
| `proxy` | Mesma tabela, comportamento diferente |
| `managed` | Django cria a tabela ou não |
| `permissions`, `default_permissions` | Permissões |
| `get_latest_by` | Campo usado por `.latest()`/`.earliest()` |
| `app_label` | A qual app o modelo pertence (quando ambíguo) |

!!! quote "📖 Na documentação oficial"
    - [Model Meta options](https://docs.djangoproject.com/en/stable/ref/models/options/)

## Recap

- A `Meta` configura a **tabela inteira**, não um campo. É um quadro de recados.
- Mais usadas: `ordering` (o `-` = decrescente), `verbose_name(_plural)`,
  `constraints` e `indexes` (as formas modernas — evite `*_together`).
- `abstract = True` cria um **modelo-receita** para reaproveitar campos via
  herança, sem tabela própria; a `Meta` é herdada pelos filhos.
- Constraints vivem no banco (última defesa); formulários dão a mensagem
  amigável (primeira defesa). Use as duas.

Modelos dominados. Agora as **[views baseadas em classe](views-cbv.md)** —
atributo por atributo, método por método.
