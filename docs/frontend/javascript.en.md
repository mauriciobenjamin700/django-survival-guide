# JavaScript from scratch

**JavaScript** (JS) is the **behavior**: reacting to clicks, changing the page
without reloading, fetching data from the server. It's the only one of the three
that's real **programming** — it has variables, conditions, functions.

!!! quote "Think like a child 🧒"
    If HTML is the house and CSS the decoration, JS is the **electricity**: the
    switch that turns on the light, the doorbell that rings, the door that opens
    when someone arrives. Without JS the house exists and is pretty; with JS it
    **reacts** to you.

## Where JS lives

```html
<!-- separate file, at the end of the body, with defer -->
<script src="app.js" defer></script>
```

!!! tip "`defer` and at the end of the `<body>`"
    `defer` makes the script run **after** the HTML has finished loading — that way
    the JS finds the elements it's going to manipulate. Without it, it runs too
    early and finds nothing. In Django, that file is a
    [static](../referencia/organizando-assets.md).

## The basics of the language

```javascript
// variables: prefer const; use let when you'll reassign
const name = "Ana";
let counter = 0;
counter = counter + 1;

// types
const text = "hi";            // string
const number = 42;            // number
const on = true;              // boolean
const list = [1, 2, 3];       // array
const person = { name: "Ana", age: 30 };  // object

// condition
if (counter > 0) {
  console.log("positive");    // console.log = prints to the console (F12)
} else {
  console.log("zero or less");
}

// function
function greet(name) {
  return `Hello, ${name}!`;   // template string with backticks
}

// arrow function — the short form
const double = (x) => x * 2;
```

!!! tip "`const` by default, `let` when you need it"
    Use `const` for everything; only switch to `let` if the value **changes**.
    Avoid the old `var` (it has confusing scope rules). This makes it clear what
    changes and what doesn't.

## The DOM: JS sees the HTML as objects

Think like a child: the browser turns your HTML into a **tree of Lego pieces**
(the **DOM**). The JS grabs a piece, changes its color, its text, or removes it.

```javascript
// find elements
const title = document.querySelector("h1");         // the first <h1>
const buttons = document.querySelectorAll(".btn");   // all with class btn

// change content and style
title.textContent = "New title";
title.style.color = "teal";

// work with classes (the preferred way to style via JS)
title.classList.add("active");
title.classList.remove("hidden");
title.classList.toggle("open");
```

| Method | What it does |
| --- | --- |
| `querySelector(css)` | Finds the **first** one matching the CSS selector |
| `querySelectorAll(css)` | Finds **all** (a list) |
| `.textContent` | Reads/changes the text |
| `.classList.add/remove/toggle` | Works with the CSS classes |
| `.setAttribute(name, value)` | Changes an attribute |

## Events: reacting to the user

Think like a child: "**when** someone presses this button, **do** this".

```javascript
const button = document.querySelector("#like");

button.addEventListener("click", () => {
  console.log("clicked!");
  button.classList.toggle("liked");
});
```

Common events: `click`, `submit` (form), `input`/`change` (fields),
`keydown` (keyboard), `DOMContentLoaded` (page ready).

### Complete example: counter

```html
<button id="plus">+1</button>
<span id="total">0</span>

<script>
  const button = document.querySelector("#plus");
  const total = document.querySelector("#total");
  let n = 0;

  button.addEventListener("click", () => {
    n = n + 1;
    total.textContent = n;
  });
</script>
```

Clicked → the number goes up, **without reloading the page**. That's JS at work.

## Intercepting a form

```javascript
const form = document.querySelector("#contact");

form.addEventListener("submit", (event) => {
  event.preventDefault();      // (1)!
  const name = form.querySelector("[name=name]").value;
  console.log("would send:", name);
});
```

1. `preventDefault()` stops the normal submit (which would reload the page) —
    useful when you want to send it via `fetch` instead. We'll come back to this
    with Django.

## `fetch`: talking to the server without reloading

Think like a child: instead of walking to the kitchen and back (reloading the
whole page), you send a **little note** asking for just what you need, and the
answer arrives while you stay at the table.

```javascript
// fetch data (GET)
async function loadPosts() {
  const response = await fetch("/api/posts/");
  const data = await response.json();      // becomes a JS object
  console.log(data.results);
}

// send data (POST) with JSON
async function createPost(post) {
  const response = await fetch("/api/posts/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(post),
  });
  return await response.json();
}
```

- **`async`/`await`** — waits for the response without freezing the page. `await`
  only inside an `async` function.
- **`.json()`** — converts the response (JSON text) into a JS object.
- **`JSON.stringify(obj)`** — converts a JS object into JSON text to send.

!!! info "This is where DRF comes in"
    That `/api/posts/` is exactly the API you built with the
    [Django REST Framework](../advanced/drf.md). The JS fetches JSON, Django
    responds with JSON — front and back talking. The details (CSRF, integration)
    are on the [next page](django-integracao.md).

## Recap

- JS is **behavior/programming**; load it with `<script defer>` at the end of the body.
- Basics: `const`/`let`, strings/numbers/arrays/objects, `if`, functions (and arrow).
- **DOM**: `querySelector`/`querySelectorAll` grab elements; change
  `textContent`, `style`, `classList`.
- **Events**: `addEventListener("click", ...)` reacts to the user;
  `preventDefault()` holds back the form submit.
- **`fetch` + `async/await`** talks to the server (GET/POST JSON) without
  reloading — the bridge to the Django API.

!!! quote "📖 In the official docs"
    - [JavaScript (MDN)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
    - [Using fetch (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)

You've got the three languages. Let's tie it all together:
**[Joining up with Django](django-integracao.md)**.
