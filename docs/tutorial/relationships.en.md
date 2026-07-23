# Relationships in depth

You already saw the three kinds of relationship in the [models](models.md). Now
let's **actually use them**: navigate from one side to the other, add and remove,
and do it without blowing up the database into a thousand queries.

!!! quote "The idea"
    A relationship is a **bridge** between two models. Django lets you cross the
    bridge in both directions: from the post to the author (`post.author`) and from
    the author to the posts (`author.posts`). The secret is knowing the name of each
    end.

## The two sides of every bridge

Every relationship has a **forward** side (where you declared the field) and a
**reverse** side (the other model). `related_name` names the reverse side.

```python
class Post(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="posts")
    tags = models.ManyToManyField(Tag, related_name="posts")
```

| From | To | How |
| --- | --- | --- |
| Post → Author | one author | `post.author` |
| Author → Posts | many posts | `author.posts.all()` |
| Post → Tags | many tags | `post.tags.all()` |
| Tag → Posts | many posts | `tag.posts.all()` |

!!! tip "Without `related_name`, Django makes one up"
    The default reverse side is `<model>_set` (e.g. `author.post_set`). Setting
    `related_name="posts"` gives you `author.posts` — much more readable. Always
    name it.

## ForeignKey (many-to-one)

```python
author = Author.objects.get(display_name="Ana")

# reverse side: a manager, with the full queryset API
author.posts.all()
author.posts.filter(status="published")
author.posts.count()
author.posts.create(title="New", body="...")   # already creates with author=author
```

!!! info "The reverse side is a *manager*, not a list"
    `author.posts` is not a ready-made list — it's a manager. That's why you chain
    `.filter()`, `.count()`, `.create()` on it, and nothing is fetched until you
    use it.

## OneToOne (one-to-one)

```python
user.author_profile          # the Author for that user
author.user                  # the User for that author
```

!!! warning "`RelatedObjectDoesNotExist` on one-to-one"
    If the `User` doesn't have an `Author` yet, accessing `user.author_profile`
    **raises an exception** (it doesn't return `None`). Guard it with
    `hasattr(user, "author_profile")` or handle the exception.

## ManyToMany (many-to-many)

The M2M manager has methods to build the relationship:

```python
post = Post.objects.get(slug="hello-world")
django = Tag.objects.get(slug="django")

post.tags.add(django)          # add (idempotent)
post.tags.remove(django)       # remove
post.tags.set([django, orm])   # replace the whole set
post.tags.clear()              # remove all
post.tags.all()                # list
```

| Method | Does |
| --- | --- |
| `.add(obj, ...)` | Adds (no duplicates) |
| `.remove(obj, ...)` | Removes |
| `.set([...])` | Swaps the whole set |
| `.clear()` | Empties |

### M2M with extra data: `through`

What if the relationship itself has attributes (e.g. *when* the tag was applied)?
Use an explicit intermediate model:

```python
class Tagging(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)


class Post(models.Model):
    tags = models.ManyToManyField(Tag, through="Tagging", related_name="posts")
```

!!! warning "With `through`, use the intermediate model to create"
    When there's a `through`, the `.add()`/`.set()` shortcuts become restricted —
    you create the link by creating a `Tagging` (which carries the extra fields).

## Querying across the bridge

The double underscore `__` crosses relationships in filters:

```python
# posts by author "Ana"
Post.objects.filter(author__display_name="Ana")

# posts with the tag whose slug is "django"
Post.objects.filter(tags__slug="django")

# authors who have at least one published post
Author.objects.filter(posts__status="published").distinct()
```

!!! tip "Watch out for duplicates when filtering by M2M/reverse"
    Filtering by a "many" relationship can repeat the main object (an author shows
    up once per matching post). Use `.distinct()` to collapse them.

## Avoiding N+1 (the part that hurts most)

```python
# ❌ N+1: one query for the list + one per author on each post
for post in Post.objects.all():
    print(post.author.display_name)

# ✅ FK/OneToOne: select_related (a single JOIN)
for post in Post.objects.select_related("author"):
    print(post.author.display_name)

# ✅ M2M/reverse: prefetch_related (matched lookups)
for post in Post.objects.prefetch_related("tags"):
    print([t.name for t in post.tags.all()])
```

!!! danger "The golden rule of relationships"
    Are you going to **iterate** and access a relationship? **FK/OneToOne →
    `select_related`**; **M2M/reverse → `prefetch_related`**. Without it, a list of
    100 items becomes 101 queries.

## Recap

- Every relationship has a forward and a reverse side; `related_name` names the
  reverse (`author.posts`).
- The reverse side and the M2M are **managers** — chain `.filter()`, `.create()`,
  etc.
- M2M: `add`/`remove`/`set`/`clear`; with extra data, use `through`.
- A missing reverse OneToOne **raises an exception** — guard it with `hasattr`.
- Cross with `__` (use `.distinct()` on M2M); escape the N+1 with
  `select_related`/`prefetch_related`.

The post list can grow a lot. Let's split it into pages: the
**[pagination](pagination.md)**.
