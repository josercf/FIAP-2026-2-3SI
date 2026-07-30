# Registro da revisão que nós fizemos - Aula 02

**Dupla revisora (nós):** (nomes dos dois integrantes)
**Dupla revisada (o PR que abrimos):** (nomes)
**URL do Pull Request revisado:** `___`
**Data:** (dd/mm/2026)

Este arquivo não é sobre o código de vocês: é sobre a **revisão que vocês
fizeram no código da dupla vizinha**. Ele é entregue junto com o Pull Request.

Um comentário só conta se disser as três coisas: **onde** (arquivo e linha),
**qual o efeito** (o que quebra, ou o que fica pior) e **qual a sugestão**
(o que fazer no lugar). "Melhorar isso aqui" não conta.

---

## 1. Como revisamos

- [ ] Lemos o diff no GitHub, arquivo por arquivo
- [ ] Rodamos o código na nossa máquina
- [ ] Rodamos `python3 sockets-l4/verificar.py` no repositório deles
- [ ] Rodamos `node http-l7/verificar.mjs` no repositório deles
- [ ] Usamos a skill `code-review` com o `ai/ask.py`

Quanto tempo levou: `___` minutos

Se rodaram os verificadores, qual foi o resultado: `___`

---

## 2. O que encontramos

Mínimo de **dois achados**. Copie o bloco para acrescentar mais.

### Achado 1

| | |
|---|---|
| Arquivo e linha | `___` |
| O que está lá hoje | `___` |
| Efeito | `___` |
| Sugestão que demos | `___` |
| Gravidade | ( ) impede o merge &nbsp; ( ) deveria mudar &nbsp; ( ) só uma ideia |
| Link do comentário no PR | `___` |

### Achado 2

| | |
|---|---|
| Arquivo e linha | `___` |
| O que está lá hoje | `___` |
| Efeito | `___` |
| Sugestão que demos | `___` |
| Gravidade | ( ) impede o merge &nbsp; ( ) deveria mudar &nbsp; ( ) só uma ideia |
| Link do comentário no PR | `___` |

---

## 3. O que a IA apontou, e o que fizemos com isso

Preencham só se usaram a skill `code-review`.

**Comando que usamos:**

```bash
___
```

| O que a skill apontou | Postamos? | Por quê |
|---|---|---|
| `___` | sim / não | `___` |
| `___` | sim / não | `___` |

**Algo que ela apontou e nós descartamos, e a razão:**

`___`

> Descartar sugestão de IA com justificativa é sinal de que vocês leram o
> código. Aceitar tudo sem checar é o oposto disso.

---

## 4. O que estava bom

Pelo menos um ponto. Revisão que só aponta defeito não ensina ninguém.

`___`

---

## 5. Nossa decisão

- [ ] Aprovado
- [ ] Aprovado com ressalvas (quais: `___`)
- [ ] Mudanças solicitadas antes do merge

**Quem clicou em aprovar:** `___`

> Quem aprova sem ler responde pelo que passou.
