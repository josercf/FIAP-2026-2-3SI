# Roteiro da apresentação de 10 minutos

Entregável da Aula 16. Escreva **quem fala o quê**, com o relógio ao lado, e
ensaie cronometrado pelo menos uma vez com a plataforma de pé.

Dez minutos é pouco. Sem roteiro escrito, um grupo de quatro pessoas gasta os
três primeiros minutos decidindo quem começa.

---

## A ordem que funciona

| Minuto | O quê | Quem fala | Tela |
|---|---|---|---|
| 0:00 - 1:00 | A dor de negócio, em uma frase, e o que a plataforma entrega | PREENCHER | slide único |
| 1:00 - 2:00 | `docker compose up -d --wait` e os treze `healthy` | PREENCHER | terminal |
| 2:00 - 4:00 | Login no Portal pelo PKCE e um pedido criado ponta a ponta | PREENCHER | navegador |
| 4:00 - 5:30 | O mesmo POST com o papel errado: 403 e a jornada | PREENCHER | terminal |
| 5:30 - 7:00 | Pergunta ao assistente com fonte citada, e a injeção recusada | PREENCHER | navegador ou terminal |
| 7:00 - 8:00 | `verificar.py` verde e o Trivy sem CRITICAL | PREENCHER | terminal |
| 8:00 - 9:00 | Uma decisão de arquitetura que vocês tomariam diferente | PREENCHER | slide único |
| 9:00 - 10:00 | Perguntas | todos | - |

Ajustem os tempos. O que não se ajusta é ter tudo escrito antes.

---

## Por que essa ordem

**Sobe primeiro.** A primeira coisa que a banca precisa ver é a plataforma de
pé, porque é a única afirmação que não dá para fazer no slide. Deixar isso para
o fim é como fica quem não ensaiou: acaba o tempo com o build rodando.

**Fluxo feliz antes do fluxo de erro.** Mostrar o 403 antes do 200 faz parecer
que algo quebrou. Mostrar o 200 e depois o 403 do mesmo endpoint com outro
usuário faz parecer o que é: o controle de acesso funcionando.

**A régua no fim.** O `verificar.py` verde fecha a apresentação com evidência,
não com opinião.

**Uma autocrítica.** Grupo que só elogia o próprio projeto parece que não
entendeu o projeto. Uma decisão que vocês tomariam diferente, com o motivo, é o
item que mais separa uma apresentação boa de uma apresentação decorada.

---

## O que costuma dar errado ao vivo, e o que fazer antes

| O que acontece | Por que | O que fazer antes |
|---|---|---|
| A plataforma não sobe na hora | Build frio, rede da faculdade, imagem não baixada | Suba **antes** da apresentação e deixe de pé. `up -d --wait` na frente da banca é para provar, não para descobrir |
| O token expirou no meio da demonstração | O access token vale 900 s | Faça o login na frente deles. É mais rápido e mostra o PKCE acontecendo |
| A porta está ocupada | Outro projeto de pé na mesma máquina | `docker ps` antes. Uma porta ocupada custa dois minutos dos dez |
| O modelo local demora e o silêncio incomoda | O Ollama sobe o modelo na primeira chamada | Faça uma pergunta de aquecimento antes de entrar |
| Ninguém sabe quem responde a pergunta | Não combinaram | Combine agora: uma pessoa por área, e ela responde mesmo que outra saiba |
| Alguém lê o slide em voz alta | Nervosismo | Slide com frase pronta é o que produz isso. Use imagem e número |
| O projetor corta a lateral do terminal | Fonte pequena e janela larga | Aumente a fonte do terminal antes. Ninguém lê 12 pt no fundo da sala |
| Passa de dez minutos | Sem ensaio | Ensaie com cronômetro. O primeiro ensaio sempre passa do tempo |

---

## O que a banca vê, mesmo sem vocês dizerem

- Se o `README` sobe a plataforma do zero em quem nunca viu o projeto.
- Se o histórico do Git tem mais de uma pessoa commitando.
- Se o que está na tela é o que está no repositório.
- Se, ao ser perguntado "por que assim?", a resposta é um motivo ou um encolher
  de ombros.

---

## Ensaio

ENSAIO_1_DURACAO: PREENCHER
ENSAIO_1_O_QUE_QUEBROU: PREENCHER
ENSAIO_2_DURACAO: PREENCHER
