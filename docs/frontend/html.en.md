# HTML from scratch

**HTML** (HyperText Markup Language) is the **structure** of the page: the text,
the images, the links, the forms — and what each piece *means*. It's not
programming; it's **markup**: you wrap the content in tags that say "this is a
heading", "this is a paragraph".

!!! quote "Think like a child 🧒"
    HTML is labeling boxes on moving day. You stick a label on each thing:
    "HEADING", "PARAGRAPH", "IMAGE", "LINK". The browser reads the labels and knows
    what each thing is and how to show it.

## The smallest possible page

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>My first site</title>
  </head>
  <body>
    <h1>Hello, world!</h1>
    <p>This is my first page.</p>
  </body>
</html>
```

Save it as `index.html`, open it in the browser — it works, with no server at all.

- **`<!doctype html>`** — announces "this is modern HTML".
- **`<html lang="en">`** — the root; `lang` helps screen readers and Google.
- **`<head>`** — information **about** the page (it doesn't show in the body): title,
  encoding, viewport (essential for mobile).
- **`<body>`** — what **appears** on the screen.

## Anatomy of a tag

Think like a child: a tag is a sandwich — open, fill, close.

```html
<p class="highlight">Content here</p>
```

- **`<p>`** opens, **`</p>`** closes (the slash `/` closes it).
- **`class="highlight"`** is an **attribute** (extra information; CSS/JS use it).
- Some tags have no filling and don't close: `<img>`, `<br>`, `<input>`.

## Essential content tags

| Tag | What it is |
| --- | --- |
| `<h1>`…`<h6>` | Headings (h1 = most important; use one h1 per page) |
| `<p>` | Paragraph |
| `<a href="...">` | Link |
| `<img src="..." alt="...">` | Image (`alt` = text if it doesn't load / screen reader) |
| `<ul>` / `<ol>` / `<li>` | Unordered list / ordered list / item |
| `<strong>` / `<em>` | Important (bold) / emphasis (italic) |
| `<br>` / `<hr>` | Line break / dividing line |

```html
<h1>Blog</h1>
<p>Welcome to <strong>my blog</strong>.</p>
<a href="https://djangoproject.com">Visit Django</a>
<img src="logo.png" alt="Blog logo">
<ul>
  <li>First item</li>
  <li>Second item</li>
</ul>
```

!!! danger "Always write the image's `alt`"
    The `alt` describes the image for people using a screen reader and appears if
    the image fails. An image without `alt` is an accessibility barrier. If the
    image is pure decoration, use `alt=""` (empty, on purpose).

## Semantic HTML: tags with meaning

Think like a child: instead of identical numbered boxes, you use **labeled**
boxes — "KITCHEN", "BEDROOM". The browser, Google and screen readers understand
the page.

```html
<body>
  <header>Top: logo and menu</header>
  <nav>Navigation links</nav>
  <main>
    <article>
      <h2>Post title</h2>
      <p>Content...</p>
    </article>
  </main>
  <footer>Footer: contact, rights</footer>
</body>
```

| Semantic tag | Role |
| --- | --- |
| `<header>` | Top (logo, title) |
| `<nav>` | Navigation (link menu) |
| `<main>` | Main content (one per page) |
| `<article>` | Independent content (a post, a card) |
| `<section>` | A thematic section |
| `<aside>` | Side content (related items) |
| `<footer>` | Footer |

!!! tip "Prefer semantics over a generic `<div>`"
    `<div>` is a box **with no meaning** — use it when no semantic tag fits.
    `<header>`, `<nav>`, `<main>` etc. say *what* the content is, which helps
    accessibility and SEO. Semantics first; `<div>` as a last resort.

## Forms: how the user sends data

This is the piece that talks to Django the most — it's how the user types in and
**sends** information.

```html
<form action="/contact/" method="post">
  <label for="name">Name</label>
  <input type="text" id="name" name="name" required>

  <label for="email">Email</label>
  <input type="email" id="email" name="email" required>

  <label for="msg">Message</label>
  <textarea id="msg" name="message" rows="4"></textarea>

  <button type="submit">Send</button>
</form>
```

- **`action`** — where to send it (a Django URL).
- **`method`** — `get` (data in the URL, for searches) or `post` (data in the body,
  for creating/changing).
- **`name`** — the key the data arrives under on the server. **Without `name`, the
  data isn't sent.**
- **`label` + `for`/`id`** — links the label to the field (clicking the text focuses
  the field; essential for accessibility).
- **`required`** — the browser blocks an empty submit (basic client-side validation).

Useful `input` types: `text`, `email`, `password`, `number`, `date`,
`checkbox`, `radio`, `file`, `hidden`.

!!! info "This is what Django receives"
    When the user clicks Send, the browser sends each field by its `name`. In
    Django, `request.POST["name"]` grabs the value — but you almost never do that
    by hand: [Django forms](../tutorial/forms.md) generate this HTML and validate
    it for you. Understanding the raw HTML helps you know what Django is doing
    underneath.

## Comments and nesting

```html
<!-- this is a comment: the browser ignores it -->
<div>
  <p>Tags <strong>inside</strong> tags: nesting.</p>
</div>
```

!!! warning "Close in the right order"
    You opened `<div><p>`, so close `</p></div>` (the inner one first). A badly
    closed tag makes the browser "guess" and the layout breaks in strange ways.

## Recap

- HTML is **markup**: tags that give structure and meaning to the content.
- Every page has a `<head>` (about) and a `<body>` (visible); tags open and close.
- Content: `<h1>`–`<h6>`, `<p>`, `<a>`, `<img alt>`, lists, `<strong>`/`<em>`.
- **Semantics** (`<header>`/`<nav>`/`<main>`/`<article>`/`<footer>`) before
  `<div>`.
- **Forms** (`<form>`, `<input name>`, `<label for>`, `<button>`) are the bridge
  to Django — the `name` is the key of the data.

!!! quote "📖 In the official docs"
    - [HTML (MDN)](https://developer.mozilla.org/en-US/docs/Web/HTML)
    - [HTML forms (MDN)](https://developer.mozilla.org/en-US/docs/Learn/Forms)

Structure is ready. Let's make it pretty: **[CSS from scratch](css.md)**.
