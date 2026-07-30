# ADR-001: Votação ao vivo nos quizzes em serviço apartado

- **Data:** 2026-07-30
- **Status:** Proposta
- **Decisores:** Prof. José Romualdo da Costa Filho

## Contexto

Os decks das aulas são páginas estáticas em Reveal.js publicadas no GitHub Pages. Os quizzes de verificação existem em todos os 13 decks, mas até esta data eram puramente decorativos: o markup `<li data-correct="true">` não era reconhecido pelo `fiap-quiz.js`, que só tratava os padrões `label > input[type=radio]` e `button.quiz-option`. Nenhum clique era registrado e o feedback nunca aparecia.

Além do conserto, o objetivo pedagógico é maior: durante a aula, os alunos devem **votar pelo celular apontando a câmera para um QR code**, e o slide deve preencher uma barra de resultado em tempo real conforme os votos chegam. Isso mede a compreensão da turma inteira, e não apenas de quem responde em voz alta.

Um agregador de votos exige estado compartilhado entre dezenas de dispositivos e uma via de atualização ao vivo, coisas que o GitHub Pages não oferece: ele serve apenas arquivos estáticos, sem execução server-side e sem persistência.

## Decisão

A votação ao vivo será implementada como um **serviço apartado, em repositório próprio**, consumido pelos decks via um pequeno cliente JavaScript. Os decks permanecem estáticos e continuam funcionando sem o serviço.

## Motivações

- **O deck não pode depender do serviço.** As aulas precisam abrir e funcionar offline, em sala sem rede ou anos depois. Sem o serviço no ar, o quiz degrada para o modo clique-e-veja-o-gabarito, que já funciona hoje.
- **Ciclo de vida diferente.** O material didático é versionado por semestre e raramente muda; um serviço com backend tem deploy, credenciais, monitoramento e custo. Misturar os dois no mesmo repositório contamina o acervo com preocupações de infraestrutura.
- **Reaproveitamento.** O mesmo serviço serve as demais disciplinas e semestres, e pode virar material de aula sobre SSE, o tema da Aula 02.
- **Publicação.** O repositório do acervo é público e o workflow envia a árvore inteira para o Pages. Qualquer segredo de backend commitado aqui vaza.

## Arquitetura proposta

```
Deck (GitHub Pages, estático)          Serviço de votação (repo apartado)
  quiz-slide                             POST /sessions            abre sessão da questão
    QR -> /v/<sessionId>       ----->    POST /sessions/:id/votes  registra voto do aluno
    barra de resultado         <-----    GET  /sessions/:id/stream  SSE com a apuração
```

- **Transporte da apuração:** SSE (`text/event-stream`), não WebSocket. O fluxo é unidirecional servidor para cliente, que é exatamente o caso de uso do SSE, e o tema já é ensinado na Aula 02. Reconexão automática vem de graça.
- **Voto:** `POST` simples com o identificador da sessão e a alternativa. Sem login: a granularidade desejada é a turma, não o aluno.
- **Estado:** efêmero, em memória, com expiração por sessão. Não há dado pessoal e não há nada a preservar depois da aula.
- **Integração no deck:** o cliente lê um `data-quiz-session` no `.quiz-container`. Ausente o atributo, ou falhando a conexão, o slide segue no comportamento local.

## Riscos conhecidos

| Risco | Mitigação |
|---|---|
| Serviço fora do ar durante a aula | O deck degrada para o modo local. O QR mostra estado de indisponível e a aula segue |
| Rede da sala instável ou bloqueando a origem | Reconexão automática do SSE; o professor pode seguir na votação por levantar a mão |
| Voto múltiplo do mesmo aluno | Aceito. A métrica é a distribuição da turma, não a nota individual. Se necessário, limitar por fingerprint de sessão no navegador |
| Custo de manter o serviço no ar | Escopo mínimo, sem banco de dados, em plataforma de free tier |
| QR placeholder ser confundido com QR real | O placeholder atual é uma moldura tracejada com o texto "em breve", não um QR escaneável |

## Consequências

**Positivas**
- Os quizzes voltam a funcionar imediatamente nos 13 decks, sem esperar o serviço.
- O acervo continua sendo um site estático, com deploy trivial e sem segredos.
- O serviço vira material de aula sobre SSE.

**Negativas**
- Dois repositórios para manter e uma integração para versionar entre eles.
- O contrato da API vira uma dependência externa dos decks; mudança quebrando exige tocar nos 13.
- Enquanto o serviço não existir, os slides exibem um QR placeholder, que precisa ser claramente identificado como tal para não frustrar a turma.

## Estado da implementação

Nesta data foi entregue apenas a parte que não depende do serviço:

- `assets/js/fiap-quiz.js` passou a reconhecer o padrão `<li data-correct>` usado pelos decks, com feedback vindo de `data-correct-msg` / `data-incorrect-msg`.
- `assets/css/fiap-theme.css` ganhou os estilos de `.quiz-container`, `.quiz-question`, `.quiz-options li`, `.option-letter` e os estados de resposta, que eram referenciados pelos decks e nunca existiram.
- Timer regressivo de 60 segundos com botão de play em cada quiz, unificado em `startTimer(elementId, segundos)`.
- Área de votação com QR placeholder, pronta para receber o `data-quiz-session`.

O serviço em si permanece como trabalho futuro.
