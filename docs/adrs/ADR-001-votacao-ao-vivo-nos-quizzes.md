# ADR-001: Votação ao vivo nos quizzes em serviço apartado

- **Data:** 2026-07-30
- **Status:** Proposta
- **Decisores:** Prof. José Romualdo da Costa Filho

## Contexto

Os decks das aulas são páginas estáticas em Reveal.js publicadas no GitHub Pages. Os quizzes de verificação existem em todos os 13 decks, mas até esta data eram puramente decorativos: o markup `<li data-correct="true">` não era reconhecido pelo `fiap-quiz.js`, que só tratava os padrões `label > input[type=radio]` e `button.quiz-option`. Nenhum clique era registrado e o feedback nunca aparecia.

Além do conserto, o objetivo pedagógico é maior: durante a aula, os alunos devem **votar pelo celular apontando a câmera para um QR code**, e o slide deve preencher uma barra de resultado em tempo real conforme os votos chegam. Isso mede a compreensão da turma inteira, e não apenas de quem responde em voz alta.

Um agregador de votos exige estado compartilhado entre dezenas de dispositivos e uma via de atualização ao vivo, coisas que o GitHub Pages não oferece: ele serve apenas arquivos estáticos, sem execução server-side e sem persistência.

## Decisão

A votação ao vivo será implementada como um **produto independente, em repositório próprio e fora do contexto FIAP**, hospedado no laboratório interno (`home01`) sob o domínio **`jrcf.dev`**, e consumido pelos decks via um pequeno cliente JavaScript. Os decks permanecem estáticos e continuam funcionando sem o serviço.

O serviço não conhece FIAP, disciplina ou turma: ele expõe o conceito genérico de **sessão de votação**, para ser reutilizado em palestras, workshops e outras turmas.

## Motivações

- **O deck não pode depender do serviço.** As aulas precisam abrir e funcionar offline, em sala sem rede ou anos depois. Sem o serviço no ar, o quiz degrada para o modo clique-e-veja-o-gabarito, que já funciona hoje.
- **Ciclo de vida diferente.** O material didático é versionado por semestre e raramente muda; um serviço com backend tem deploy, credenciais, monitoramento e custo. Misturar os dois no mesmo repositório contamina o acervo com preocupações de infraestrutura.
- **Reaproveitamento fora da FIAP.** O mesmo serviço atende palestras, workshops e outras turmas. Amarrá-lo ao acervo de uma disciplina inviabilizaria isso.
- **Publicação.** O repositório do acervo é público e o workflow envia a árvore inteira para o Pages. Qualquer segredo de backend commitado aqui vaza.
- **Infraestrutura já existente.** O `home01` já roda nginx-proxy-manager com Let's Encrypt e PostgreSQL em Docker. O serviço entra como mais um container na rede `proxy-net`, sem custo marginal de infraestrutura.

## Arquitetura proposta

```
Deck (GitHub Pages, estático)        home01 / rede proxy-net
  quiz-slide                           nginx-proxy-manager  (TLS, 80/443, já existente)
    QR -> jrcf.dev/v/<id>    ----->      |
    barra de resultado       <-----      +-- voting-api   POST /sessions
                                         |                POST /sessions/:id/votes
                                         |                GET  /sessions/:id/stream  (SSE)
                                         +-- postgres     (instância já existente, 5432)
```

Hospedagem no `home01` (Ubuntu 24.04, 4 vCPU, 7,7 GB RAM), aproveitando o que já roda lá:

- **`nginx-proxy-manager`** já publica 80/443 e gerencia certificados; basta um proxy host novo para o subdomínio.
- **`postgres`** já está no ar em `~/infra/docker-compose.yml`, na rede `proxy-net`. Basta um database dedicado.
- **Subdomínio sugerido:** `vote.jrcf.dev`, ou `quiz.jrcf.dev`.

- **Transporte da apuração:** SSE (`text/event-stream`), não WebSocket. O fluxo é unidirecional servidor para cliente, que é exatamente o caso de uso do SSE, e o tema já é ensinado na Aula 02. Reconexão automática vem de graça.
- **Voto:** `POST` simples com o identificador da sessão e a alternativa. Sem login: a granularidade desejada é a turma, não o aluno.
- **Estado:** sessões e votos na instância PostgreSQL existente, com expiração automática. Não há dado pessoal e nada precisa sobreviver ao semestre.
- **Integração no deck:** o cliente lê um `data-quiz-session` no `.quiz-container`. Ausente o atributo, ou falhando a conexão, o slide segue no comportamento local.

## Riscos conhecidos

| Risco | Mitigação |
|---|---|
| Serviço fora do ar durante a aula | O deck degrada para o modo local. O QR mostra estado de indisponível e a aula segue |
| Rede da sala instável ou bloqueando a origem | Reconexão automática do SSE; o professor pode seguir na votação por levantar a mão |
| Voto múltiplo do mesmo aluno | Aceito. A métrica é a distribuição da turma, não a nota individual. Se necessário, limitar por fingerprint de sessão no navegador |
| `home01` indisponível durante a aula (link residencial, queda de energia) | O deck degrada para o modo local. Este é o risco mais provável de todos e é o motivo de o deck nunca poder depender do serviço |
| Expor um serviço da rede doméstica à internet | Entra atrás do nginx-proxy-manager já existente, com TLS, sem porta nova publicada e sem dado sensível trafegando |
| Disputa de recursos com os demais containers do `home01` | O host tem ~3,8 GB de RAM disponíveis e 28 GB de disco livres. O serviço é pequeno, mas convém fixar limites de CPU e memória no compose |
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
