# JavaScript do zero

**JavaScript** (JS) é o **comportamento**: reagir a cliques, mudar a página sem
recarregar, buscar dados do servidor. É a única das três que é **programação** de
verdade — tem variáveis, condições, funções.

!!! quote "Pensa como criança 🧒"
    Se o HTML é a casa e o CSS a decoração, o JS é a **eletricidade**: o
    interruptor que acende a luz, a campainha que toca, a porta que abre quando
    alguém chega. Sem JS a casa existe e é bonita; com JS ela **reage** a você.

## Onde o JS vive

```html
<!-- arquivo separado, no fim do body, com defer -->
<script src="app.js" defer></script>
```

!!! tip "`defer` e no fim do `<body>`"
    `defer` faz o script rodar **depois** que o HTML terminou de carregar — assim
    o JS encontra os elementos que vai manipular. Sem isso, ele roda cedo demais e
    não acha nada. No Django, esse arquivo é um
    [estático](../referencia/organizando-assets.md).

## O básico da linguagem

```javascript
// variáveis: prefira const; use let quando for reatribuir
const nome = "Ana";
let contador = 0;
contador = contador + 1;

// tipos
const texto = "olá";          // string
const numero = 42;            // number
const ligado = true;          // boolean
const lista = [1, 2, 3];      // array
const pessoa = { nome: "Ana", idade: 30 };  // object

// condição
if (contador > 0) {
  console.log("positivo");    // console.log = imprime no console (F12)
} else {
  console.log("zero ou menos");
}

// função
function saudar(nome) {
  return `Olá, ${nome}!`;     // template string com crase
}

// função de seta (arrow) — forma curta
const dobro = (x) => x * 2;
```

!!! tip "`const` por padrão, `let` quando precisar"
    Use `const` para tudo; só troque por `let` se o valor **muda**. Evite o antigo
    `var` (tem regras de escopo confusas). Isso deixa claro o que muda e o que não.

## O DOM: JS enxerga o HTML como objetos

Pensa como criança: o navegador transforma seu HTML numa **árvore de peças de
Lego** (o **DOM**). O JS pega uma peça, muda a cor, o texto, ou tira ela.

```javascript
// achar elementos
const titulo = document.querySelector("h1");        // o primeiro <h1>
const botoes = document.querySelectorAll(".btn");    // todos com class btn

// mudar conteúdo e estilo
titulo.textContent = "Novo título";
titulo.style.color = "teal";

// mexer em classes (o jeito preferido de estilizar via JS)
titulo.classList.add("ativo");
titulo.classList.remove("escondido");
titulo.classList.toggle("aberto");
```

| Método | Faz |
| --- | --- |
| `querySelector(css)` | Acha o **primeiro** que casa com o seletor CSS |
| `querySelectorAll(css)` | Acha **todos** (uma lista) |
| `.textContent` | Lê/muda o texto |
| `.classList.add/remove/toggle` | Mexe nas classes CSS |
| `.setAttribute(nome, valor)` | Muda um atributo |

## Eventos: reagir ao usuário

Pensa como criança: "**quando** alguém apertar este botão, **faça** isto".

```javascript
const botao = document.querySelector("#curtir");

botao.addEventListener("click", () => {
  console.log("clicou!");
  botao.classList.toggle("curtido");
});
```

Eventos comuns: `click`, `submit` (formulário), `input`/`change` (campos),
`keydown` (teclado), `DOMContentLoaded` (página pronta).

### Exemplo completo: contador

```html
<button id="mais">+1</button>
<span id="total">0</span>

<script>
  const botao = document.querySelector("#mais");
  const total = document.querySelector("#total");
  let n = 0;

  botao.addEventListener("click", () => {
    n = n + 1;
    total.textContent = n;
  });
</script>
```

Clicou → o número sobe, **sem recarregar a página**. Isso é o JS trabalhando.

## Interceptar um formulário

```javascript
const form = document.querySelector("#contato");

form.addEventListener("submit", (evento) => {
  evento.preventDefault();      // (1)!
  const nome = form.querySelector("[name=nome]").value;
  console.log("enviaria:", nome);
});
```

1. `preventDefault()` impede o envio normal (que recarregaria a página) — útil
    quando você quer enviar via `fetch` no lugar. Voltaremos a isso com Django.

## `fetch`: conversar com o servidor sem recarregar

Pensa como criança: em vez de ir até a cozinha e voltar (recarregar a página
inteira), você manda um **bilhetinho** pedindo só o que precisa, e a resposta
chega enquanto você continua na mesa.

```javascript
// buscar dados (GET)
async function carregarPosts() {
  const resposta = await fetch("/api/posts/");
  const dados = await resposta.json();     // vira objeto JS
  console.log(dados.results);
}

// enviar dados (POST) com JSON
async function criarPost(post) {
  const resposta = await fetch("/api/posts/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(post),
  });
  return await resposta.json();
}
```

- **`async`/`await`** — espera a resposta sem travar a página. `await` só dentro
  de função `async`.
- **`.json()`** — converte a resposta (texto JSON) em objeto JS.
- **`JSON.stringify(obj)`** — converte objeto JS em texto JSON para enviar.

!!! info "É aqui que o DRF entra"
    Aquele `/api/posts/` é exatamente a API que você construiu com o
    [Django REST Framework](../advanced/drf.md). O JS busca JSON, o Django
    responde JSON — front e back conversando. Detalhes (CSRF, integração) na
    [próxima página](django-integracao.md).

## Recapitulando

- JS é **comportamento/programação**; carregue com `<script defer>` no fim do body.
- Básico: `const`/`let`, strings/números/arrays/objetos, `if`, funções (e arrow).
- **DOM**: `querySelector`/`querySelectorAll` pegam elementos; mude
  `textContent`, `style`, `classList`.
- **Eventos**: `addEventListener("click", ...)` reage ao usuário;
  `preventDefault()` segura o envio do form.
- **`fetch` + `async/await`** conversa com o servidor (GET/POST JSON) sem
  recarregar — a ponte para a API do Django.

!!! quote "📖 Na documentação oficial"
    - [JavaScript (MDN)](https://developer.mozilla.org/pt-BR/docs/Web/JavaScript)
    - [Usando o fetch (MDN)](https://developer.mozilla.org/pt-BR/docs/Web/API/Fetch_API/Using_Fetch)

Você tem as três linguagens. Bora amarrar tudo:
**[Juntando com Django](django-integracao.md)**.
