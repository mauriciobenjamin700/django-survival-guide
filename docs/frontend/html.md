# HTML do zero

**HTML** (HyperText Markup Language) é a **estrutura** da página: o texto, as
imagens, os links, os formulários — e o que cada pedaço *significa*. Não é
programação; é **marcação**: você envolve o conteúdo em etiquetas que dizem "isto
é um título", "isto é um parágrafo".

!!! quote "Pensa como criança 🧒"
    HTML é etiquetar caixas na mudança. Você põe um adesivo em cada coisa:
    "TÍTULO", "PARÁGRAFO", "IMAGEM", "LINK". O navegador lê os adesivos e sabe o
    que cada coisa é e como mostrar.

## A menor página possível

```html
<!doctype html>
<html lang="pt-br">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Meu primeiro site</title>
  </head>
  <body>
    <h1>Olá, mundo!</h1>
    <p>Esta é a minha primeira página.</p>
  </body>
</html>
```

Salve como `index.html`, abra no navegador — funciona, sem servidor nenhum.

- **`<!doctype html>`** — avisa "isto é HTML moderno".
- **`<html lang="pt-br">`** — a raiz; `lang` ajuda leitores de tela e o Google.
- **`<head>`** — informações **sobre** a página (não aparecem no corpo): título,
  codificação, viewport (essencial para celular).
- **`<body>`** — o que **aparece** na tela.

## Anatomia de uma tag

Pensa como criança: uma tag é um sanduíche — abre, recheia, fecha.

```html
<p class="destaque">Conteúdo aqui</p>
```

- **`<p>`** abre, **`</p>`** fecha (a barra `/` fecha).
- **`class="destaque"`** é um **atributo** (informação extra; o CSS/JS usam).
- Algumas tags não têm recheio e não fecham: `<img>`, `<br>`, `<input>`.

## Tags de conteúdo essenciais

| Tag | O que é |
| --- | --- |
| `<h1>`…`<h6>` | Títulos (h1 = mais importante; use um h1 por página) |
| `<p>` | Parágrafo |
| `<a href="...">` | Link |
| `<img src="..." alt="...">` | Imagem (`alt` = texto se não carregar / leitor de tela) |
| `<ul>` / `<ol>` / `<li>` | Lista sem ordem / ordenada / item |
| `<strong>` / `<em>` | Importante (negrito) / ênfase (itálico) |
| `<br>` / `<hr>` | Quebra de linha / linha divisória |

```html
<h1>Blog</h1>
<p>Bem-vindo ao <strong>meu blog</strong>.</p>
<a href="https://djangoproject.com">Visite o Django</a>
<img src="logo.png" alt="Logo do blog">
<ul>
  <li>Primeiro item</li>
  <li>Segundo item</li>
</ul>
```

!!! danger "Sempre escreva o `alt` da imagem"
    O `alt` descreve a imagem para quem usa leitor de tela e aparece se a imagem
    falhar. Imagem sem `alt` é barreira de acessibilidade. Se a imagem é pura
    decoração, use `alt=""` (vazio, de propósito).

## HTML semântico: etiquetas com significado

Pensa como criança: em vez de caixas iguais numeradas, você usa caixas
**rotuladas** — "COZINHA", "QUARTO". O navegador, o Google e os leitores de tela
entendem a página.

```html
<body>
  <header>Topo: logo e menu</header>
  <nav>Links de navegação</nav>
  <main>
    <article>
      <h2>Título do post</h2>
      <p>Conteúdo...</p>
    </article>
  </main>
  <footer>Rodapé: contato, direitos</footer>
</body>
```

| Tag semântica | Papel |
| --- | --- |
| `<header>` | Topo (logo, título) |
| `<nav>` | Navegação (menu de links) |
| `<main>` | Conteúdo principal (um por página) |
| `<article>` | Conteúdo independente (um post, um card) |
| `<section>` | Uma seção temática |
| `<aside>` | Conteúdo lateral (relacionados) |
| `<footer>` | Rodapé |

!!! tip "Prefira semântica a `<div>` genérica"
    `<div>` é uma caixa **sem significado** — use quando nenhuma tag semântica
    serve. `<header>`, `<nav>`, `<main>` etc. dizem *o que* o conteúdo é, o que
    ajuda acessibilidade e SEO. Semântica primeiro; `<div>` como último recurso.

## Formulários: como o usuário envia dados

Este é o pedaço que mais conversa com o Django — é por aqui que o usuário digita
e **envia** informação.

```html
<form action="/contato/" method="post">
  <label for="nome">Nome</label>
  <input type="text" id="nome" name="nome" required>

  <label for="email">E-mail</label>
  <input type="email" id="email" name="email" required>

  <label for="msg">Mensagem</label>
  <textarea id="msg" name="mensagem" rows="4"></textarea>

  <button type="submit">Enviar</button>
</form>
```

- **`action`** — para onde enviar (uma URL do Django).
- **`method`** — `get` (dados na URL, para buscas) ou `post` (dados no corpo,
  para criar/alterar).
- **`name`** — a chave com que o dado chega no servidor. **Sem `name`, o dado não
  é enviado.**
- **`label` + `for`/`id`** — liga o rótulo ao campo (clicar no texto foca o campo;
  essencial para acessibilidade).
- **`required`** — o navegador barra o envio vazio (validação básica, do lado do
  cliente).

Tipos de `input` úteis: `text`, `email`, `password`, `number`, `date`,
`checkbox`, `radio`, `file`, `hidden`.

!!! info "É isto que o Django recebe"
    Quando o usuário clica em Enviar, o navegador manda cada campo pelo `name`. No
    Django, `request.POST["nome"]` pega o valor — mas você quase nunca faz isso na
    mão: os [formulários do Django](../tutorial/forms.md) geram esse HTML e
    validam para você. Entender o HTML cru ajuda a saber o que o Django está
    fazendo por baixo.

## Comentários e aninhamento

```html
<!-- isto é um comentário: o navegador ignora -->
<div>
  <p>Tags <strong>dentro</strong> de tags: aninhamento.</p>
</div>
```

!!! warning "Feche na ordem certa"
    Abriu `<div><p>`, feche `</p></div>` (o de dentro primeiro). Tag mal fechada
    faz o navegador "adivinhar" e o layout quebra de formas estranhas.

## Recapitulando

- HTML é **marcação**: etiquetas que dão estrutura e significado ao conteúdo.
- Toda página tem `<head>` (sobre) e `<body>` (visível); tags abrem e fecham.
- Conteúdo: `<h1>`–`<h6>`, `<p>`, `<a>`, `<img alt>`, listas, `<strong>`/`<em>`.
- **Semântica** (`<header>`/`<nav>`/`<main>`/`<article>`/`<footer>`) antes de
  `<div>`.
- **Formulários** (`<form>`, `<input name>`, `<label for>`, `<button>`) são a
  ponte com o Django — o `name` é a chave do dado.

!!! quote "📖 Na documentação oficial"
    - [HTML (MDN)](https://developer.mozilla.org/pt-BR/docs/Web/HTML)
    - [Formulários HTML (MDN)](https://developer.mozilla.org/pt-BR/docs/Learn/Forms)

Estrutura pronta. Bora deixar bonito: **[CSS do zero](css.md)**.
