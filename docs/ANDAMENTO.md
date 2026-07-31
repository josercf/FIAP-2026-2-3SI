# Andamento do acervo

Estado do trabalho para retomar em uma sessão nova. Atualize este arquivo ao fim de cada sessão.

**Última atualização:** 31/07/2026 (Módulo III construído)

---

## Primeiro: leia isto ao abrir a sessão

1. `CLAUDE.md` — comandos, arquitetura do acervo e armadilhas conhecidas.
2. `.claude/agents/construtor-aulas.md` — metodologia consolidada para construir aula.
3. Este arquivo.

Push do acervo **exige a chave do josercf**, senão o GitHub autentica como `canaldoovidio` e nega:

```bash
# O -F /dev/null nao e enfeite: sem ele o ~/.ssh/config manda o github.com para a
# outra identidade e o push falha com "denied to canaldoovidio", mesmo com -i.
GIT_SSH_COMMAND='ssh -i ~/.ssh/id_ed25519_josercf -o IdentitiesOnly=yes -F /dev/null' git push
```

---

## Onde está cada coisa

| | |
|---|---|
| Acervo | <https://github.com/josercf/FIAP-2026-2-3SI> |
| Portal publicado | <https://josercf.github.io/FIAP-2026-2-3SI/> |
| Labs | `josercf/mwe-2026-2-labNN-tema`, 13 repositórios públicos |
| Skills compartilhadas | <https://github.com/josercf/skill-library> |
| Lab interno | `ssh josercf@home01`, domínio `jrcf.dev` |

---

## Concluído

### Aula 01 — pronta e publicada

41 slides, validados em 1280x720, no ar em
<https://josercf.github.io/FIAP-2026-2-3SI/aulas-1sem/aulas/aula01.html>.

Foi refeita a partir do feedback do professor: foto real de família no slide de apresentação, texto oficial da FIAP no objetivo, slide de SDD corrigido para **Spec Driven Development**, Bounded Contexts dividido em dois com diagramas, o Multiverso do Git dividido em três (analogia, anatomia de um commit, o que é uma branch), atividade prática em cinco slides começando por fork do Lab Kit, e slide de entrega com o Microsoft Forms embedado.

### Infraestrutura de laboratório

13 repositórios públicos criados, um por aula com lab, autocontidos:

- devcontainer sobre a imagem oficial da stack, com **Ollama e `qwen2.5:1.5b` já baixados** na criação
- `ai/ask.py` sem dependências: fala só com o **Ollama local** do devcontainer (o GitHub Models foi retirado em 30/07/2026, ver ADR-005 e o registro histórico abaixo)
- README com missão no case LogiTech, passo a passo e entregáveis com valor numérico
- fluxo por **fork**, não clone

Gerados por `tools/scaffold_labs.py` (respeita `LABS_OUT`).

**Registro histórico:** em sessão de 30/07/2026 (manhã) o GitHub Models respondia com o token do professor. No mesmo dia o serviço entrou em brownout de aposentadoria (HTTP 410) e deixou de ser opção: o Ollama local virou o único backend de IA dos 13 laboratórios, decisão registrada na `ADR-005-fim-do-github-models-e-ollama-como-unico-backend.md`. O scaffolder e o `ai/ask.py` gerados já não mencionam o serviço.

### Automação

- **`tools/check_slides.py`** — validador Playwright. Compara o retângulo de cada descendente com a área útil do slide. Achou 6 slides estourando na Aula 01 que passavam despercebidos.
- **Hook `PostToolUse`** em `.claude/settings.json` — roda o validador ao editar qualquer `aulas/aula*.html`.
- **Agente `construtor-aulas`** — constrói aula inteira seguindo a metodologia.
- **Agente `revisor-slides`** — revisa deck de forma independente.

### Decisões registradas

`docs/adrs/ADR-001-votacao-ao-vivo-nos-quizzes.md` — **Aceita e publicada.** A votação ao vivo (serviço Pulso, repositório `josercf/pulso`) está no ar em `vote.jrcf.dev` desde 31/07/2026. As aulas 01, 02 e 03 carregam o `client.js` com `defer` e ligam os quizzes por `data-quiz-key="aulaNN-quizN"`; o QR placeholder permanece no markup como fallback. Aulas novas devem repetir esse padrão.

`docs/adrs/ADR-008-contratos-compartilhados-do-modulo-III.md`, contrato do Módulo III: os quatro serviços novos, **CORS no contrato de todo backend chamado por navegador**, PostgreSQL virando `pgvector/pgvector:pg16`, embeddings em 768 dimensões, e a decisão de que **SQL relacional é conteúdo da Aula 12**, não pré-requisito dela. Emendada no mesmo dia, por medição, trocando o modelo de embedding padrão.

`docs/adrs/ADR-004-formato-progressivo-da-aula-03.md` — a Aula 03 abandona o formato teoria + laboratório único e adota sete ciclos de teoria + prática individual, com verificador progressivo e diretório de resgate.

`docs/adrs/ADR-005-fim-do-github-models-e-ollama-como-unico-backend.md` — o GitHub Models foi retirado em 30/07/2026; o Ollama local é o único backend de IA dos laboratórios, com modelo por lab (`qwen2.5:1.5b` no geral, `qwen3.5:2b` no lab03).

`docs/adrs/ADR-002-escopo-do-laboratorio-da-aula-02.md` — **Aceita.** O laboratório da Aula 02 entrega o coletor de sockets L4 pronto e troca o relatório de captura por três medições numéricas com `cURL`. O **Wireshark saiu do programa da disciplina**, não só do laboratório, por decisão do professor em 30/07/2026. A comunicação entre o coletor e o gateway é por arquivo JSON Lines, simplificação declarada, a ser substituída na Aula 07.

---

### Aula 02 — pronta, publicada e com o repositório de lab sincronizado

35 slides validados em 1280x720, com diagramas SVG inline para a evolução do HTTP,
o handshake TLS e o fluxo do SSE. Lab Kit completo em `aulas-1sem/labs/aula02-lab/`.

O escopo do laboratório está em duas ADRs. A
`ADR-002-escopo-do-laboratorio-da-aula-02.md` tirou o Wireshark e trocou o
relatório de captura por três medições numéricas com `cURL`. A
`ADR-003-o-aluno-escreve-o-coletor-l4-na-aula-02.md` **superou a decisão 1 da
002**: o aluno passou a completar o coletor L4 em vez de recebê-lo pronto.

**Por que a 003 existe:** o slide do Desafio do Mini Mundo afirmava que "depois da
Aula 01 temos um processo Python escutando na 8081", o que era falso, já que a
Aula 01 entregou só PRD e SDD. Corrigir só o texto deixaria de pé o problema
maior, que a própria ADR-002 tinha registrado como risco: o aluno chegaria ao CP1,
uma prova prática individual que cobra Sockets TCP/UDP, sem nunca ter escrito um.
O coletor virou esqueleto com quatro TODO no lado UDP, com o lado TCP pronto como
modelo, e ganhou `sockets-l4/verificar.py` com cinco critérios. O laboratório foi
de 60 para 64 minutos, dentro dos ~75 do Bloco 2.

**Revisão de código assistida por IA.** A skill `code-review` foi importada de
`awesome-skills/code-review-skill` (MIT) para `josercf/skill-library`, com
`ORIGEM.md` registrando procedência, licença e commit. Entrou um slide novo com
instalação e exemplos de uso, e a revisão virou entregável: `docs/CODE_REVIEW.md`
pede qual PR foi revisado, como, o que se encontrou e qual sugestão foi dada,
incluindo o que a IA sugeriu e a dupla **descartou**, com a razão.

Validado de ponta a ponta **dentro da imagem do devcontainer**
(`typescript-node:1-22-bookworm`, que traz Python 3.11, Node 22 e `cURL`), nas
quatro combinações:

| | esqueleto entregue | gabarito |
|---|---|---|
| `sockets-l4/verificar.py` | 0 de 5, sai com 1 | 5 de 5, sai com 0 |
| `http-l7/verificar.mjs` | 1 de 7, sai com 1 | 7 de 7, sai com 0 |

A cadeia completa também roda: coletor do gabarito alimentando o gateway do
gabarito. Os dois verificadores discriminam de verdade.

As animações por clique dos slides 9 e 19 são conferidas em navegador: nada
visível antes do primeiro avanço, e um grupo por vez depois. `fragment` dentro de
SVG funciona, mas não é óbvio, então existe teste.

O formulário de entrega está publicado: <https://forms.cloud.microsoft/r/ykGYKsPAj7>,
embutido no slide 32 e citado no README do lab.

**O repositório que o aluno forka foi sincronizado**, em
<https://github.com/josercf/mwe-2026-2-lab02-http-sse>. Ele tinha só o esqueleto do
scaffolder, com um README que ainda mandava implementar os sockets e capturar
tráfego com Wireshark. Agora traz `sockets-l4/`, `http-l7/`, `docs/OBSERVACOES.md` e
o README real, **sem o `gabarito/`**.

> **Atenção ao publicar qualquer aula:** o repositório de lab é separado do acervo
> e **não é sincronizado por nada automático**. Depois de mexer em
> `aulas-1sem/labs/aulaXX-lab/`, é preciso clonar `josercf/mwe-2026-2-labNN-tema`,
> copiar o conteúdo (nunca o `gabarito/`), preservar `.devcontainer/` e `ai/ask.py`,
> e dar push. Foi assim que a Aula 02 foi sincronizada.

### Aula 03 — pronta, validada e revisada (31/07/2026)

Deck de 55 slides em sete ciclos progressivos (ADR-004), com nove animações
SVG, três quizzes ligados ao Pulso e sete slides de atividade espelhando o
`verificar.py`. Validado em 1280x720 e revisado pelo `revisor-slides`; a
revisão moveu os quizzes de multi-stage e volumes para depois dos ciclos que
os ensinam e renomeou o marcador `MOUNTS_DENTRO` para `ENTRADAS_PROC_DENTRO`.

Lab kit completo em `aulas-1sem/labs/aula03-lab/`: serviços congelados da
Aula 02, baseline de medição, `resgate/`, verificador com sete critérios
(0 de 7 no esqueleto, suíte com 24 testes), skill `logitech-dockerfile`,
`agente.yaml` (Ollama, `qwen3.5:2b`) e devcontainer testado de ponta a ponta
na imagem oficial (222 s, incluindo o download do modelo e do `docker-agent`).

Números medidos (arm64): coletor 1638,4 MB -> 78,9 MB (95,2%); gateway
1658,9 MB -> 229,0 MB (86,2%). Critérios do entregável: redução mínima de
80% nos dois, absoluto de 100 MB só no coletor.

Armadilhas fechadas nesta construção: o instalador do Ollama passou a exigir
`zstd`, que a imagem do devcontainer não traz (o post-create gerado instala
antes); e os curls de download ganharam `--connect-timeout`/`--max-time`,
porque execuções anteriores travaram em curl sem timeout contra o GitHub.

### Módulo II completo: Aulas 05 a 08 (31/07/2026)

As quatro aulas de setembro foram construídas na mesma sessão, em paralelo, e é
a primeira vez que aulas do acervo **dependem umas das outras**: a 07 orquestra
o que a 05 e a 06 constroem, e a 08 chama a API de Pedidos da 05. Por isso o
contrato veio antes do conteúdo, na `ADR-006`.

| Aula | Deck | Laboratório |
|---|---|---|
| 05, POO e SOLID | 51 slides, 17 figuras (10 animadas) | Pedidos em Spring Boot 3 e Faturamento em .NET 8, seis lacunas, verificador com 11 critérios |
| 06, Padrões estruturais | 57 slides, 11 figuras animadas | Frete em FastAPI e Notificações em Node/TS, seis lacunas, 8 critérios, 33 testes |
| 07, Compose e AI Gateway | 53 slides, 9 animações | Oito serviços orquestrados, AI Gateway com Facade e Strategy, 5 critérios |
| 08, Function Calling | 52 slides, 9 animações | Agente com Command e JSON Schema, worktrees, 9 critérios, 42 testes |

**Números medidos, não estimados.** Race condition do Singleton na Aula 05: 35,
41 e 44 notas fiscais duplicadas em três execuções no Mac, 19 num contêiner com
dois núcleos. Compose da Aula 07: 11,9 s até os oito serviços saudáveis e 228 MB
somados em repouso, contra 1632 MB de teto declarado, em arm64 com 10 núcleos.
Tool calling do modelo local na Aula 08: 6 de 6 acertos com descrição boa da
ferramenta, 0 de 3 com a descrição enfraquecida.

**Defeitos reais encontrados durante a construção**, todos corrigidos e a maioria
virando conteúdo: healthcheck com `localhost` deixava 4 dos 8 serviços
`unhealthy`, porque no Alpine ele resolve primeiro para IPv6 (`ADR-007`); o
numerador de notas reiniciava a cada boot e colidia com o índice único; conexão
JDBC única expirava depois de 45 minutos ociosa; seis animações da Aula 07 tinham
`keyTimes` que não terminavam em 1 e eram descartadas pelo navegador; o
verificador da Aula 08 aprovava por engano quando outro serviço ocupava a 8080.

**O que a revisão independente pegou e foi corrigido.** Na Aula 06: código do
decorator que não compilava com `strict`, bloco de comandos que quebrava se
colado inteiro, saída do verificador **editada passando por real** no slide que
se vende como a régua pública, ligaduras da JetBrains Mono projetando `<=` como
`≤` em slides onde o aluno digita a sintaxe, e caminhos de arquivo subindo para
maiúscula por causa do `text-transform` do tema.

**Decisão pedagógica que custa e está registrada** (`ADR-007`): o Compose da
Aula 07 orquestra serviços **mínimos** por padrão, porque conteinerizar Spring
Boot e .NET colocaria build de Maven e NuGet dentro de um laboratório de 60
minutos. O kit traz um caminho de troca testado, com Dockerfiles multi-stage
para os serviços reais, para quem completou as Aulas 05 e 06 subir a própria
implementação.

### Módulo III completo: Aulas 10, 11 e 12 (31/07/2026)

Construídas em paralelo, na mesma sessão, com o contrato escrito antes na
`ADR-008`. A interdependência é a mesma do Módulo II, e uma novidade: **a partir
da Aula 10 o consumidor das APIs é o navegador**, que aplica a política de mesma
origem. Nenhum serviço das Aulas 02, 05 e 06 tinha sido escrito com isso em
mente, então CORS entrou no contrato antes de virar aula de conserto.

| Aula | Deck | Laboratório |
|---|---|---|
| 10, TDD e React | 53 slides, 13 figuras (6 animadas) | Suíte de unidade sobre o frete com Stub, Mock e Spy, mais o Portal do Cliente em React 19, seis lacunas, 8 critérios |
| 11, Angular e RxJS | 52 slides, 17 figuras, 82 animações | Painel administrativo com frota em tempo real e faturamento, seis lacunas, 8 critérios, 31 testes |
| 12, do relacional ao vetorial | 57 slides, 9 figuras (4 animadas) | SQL à mão, `pgvector`, RAG com citação da fonte e servidor MCP, seis lacunas, 7 critérios, 23 testes |

**A Aula 12 mudou de escopo, e é a decisão pedagógica do módulo.** O levantamento
feito ao escrever a `ADR-008` mostrou que **não existia um único arquivo `.sql`
no acervo**: o schema nascia do `ddl-auto` do Hibernate e do `ModelBuilder` do EF
Core, e o aluno chegava a outubro tendo persistido em PostgreSQL o semestre
inteiro sem escrever SQL. A aula virou "PostgreSQL: do relacional ao vetorial",
com a busca semântica entrando como **mais um `ORDER BY`**, sobre distância. O
servidor MCP encolheu para o último terço do bloco prático, e a Pergunta de
Verificação 3 deixou de cobrar a lista de conceitos do MCP para cobrar índice,
`EXPLAIN` e a natureza **aproximada** do HNSW.

**Números medidos, não estimados.** `EXPLAIN` com 50.000 vetores: `Seq Scan` em
389,933 ms contra `Index Scan` em 1,005 ms, com o índice ocupando 161 MB contra
2944 kB da tabela. Cancelamento do `switchMap` na Aula 11, observado nos dois
lados: 4 requisições recebidas e 4 concluídas com `mergeMap`, contra 4 recebidas,
1 concluída e 3 canceladas com `switchMap`. Aula 10: `verificar.py` 0 de 8 no
esqueleto e 8 de 8 no resgate, com sete mutantes discriminando critério a
critério.

**Uma decisão minha foi derrubada por medição.** A `ADR-008` fixava
`nomic-embed-text` para os embeddings. A construção mediu `recall@3` em treze
perguntas de resposta conhecida: 9 de 13 para o `nomic`, **13 de 13** para o
`paraphrase-multilingual`, que tem as mesmas 768 dimensões. O modelo é treinado
predominantemente em inglês e o acervo é contrato de transporte em português
jurídico. Mais instrutivo ainda: seguir a recomendação do próprio fornecedor,
prefixando a consulta com `search_query:`, **piorou** para 7 de 13, em silêncio.
A ADR foi emendada e isso virou conteúdo do slide 22.

**Defeitos reais encontrados durante a construção**, todos corrigidos: teste do
resgate **tautológico** na Aula 10, que calculava o esperado importando a
constante do código sob teste e deixava o mutante sobreviver; lacuna que **não
discriminava** na Aula 11, porque o Angular 22 resolve o `HttpClient` sem
`provideHttpClient()` e o critério passaria intocado; `verificar.py` da Aula 11
reprovando código correto por ancorar na chamada em vez da declaração do método;
e o `EXPLAIN` da Aula 12 que **nunca usaria o índice**, porque a consulta tirava
o vetor de comparação de uma subconsulta.

**O que a revisão independente pegou.** Ligadura da JetBrains Mono comendo o
`=>` na Aula 10, que **não tinha regra nenhuma** de bloqueio, nem para código nem
para SVG, numa aula de React; a mesma ligadura escapando dentro de `<text>` de
SVG na Aula 12, onde o operador `<=>` virava glifo de seta dupla, porque a regra
do tema alcança `pre`, `code` e `.mono` mas não SVG; dois links da MDN em pt-BR
com 404 de verdade na Aula 11 e o blog da Nomic morto na Aula 12; e os Quizzes 2
e 3 da Aula 12 fora de sincronia com o planejamento, que **eu** havia emendado
depois que o deck ficou pronto.

### O validador ganhou uma terceira checagem (31/07/2026)

`tools/check_slides.py` passou a detectar **TITULO NO LOGO**: título longo que
quebra a segunda linha por baixo do logo da FIAP. Isso cabia nos 720px e não
sobrepunha filho direto da `section`, então passava pelas duas checagens
anteriores. O logo fica fora da checagem de sobreposição de propósito, senão todo
slide daria falso positivo, e esse era o ponto cego.

Apareceu em dois dos três decks novos e só foi visto porque um revisor abriu o
slide no navegador. A checagem compara as caixas de **linha** do título, não a
caixa do `h2`, que costuma ser larga e vazia à direita.

### Saneamento do acervo (30/07/2026)

- **Os 13 decks passavam no `check_slides.py` nesta data.** Em 31/07/2026 isso
  deixou de ser verdade para as Aulas 05 e 06, ver as pendências técnicas.
  Havia 5 slides de hands-on estourando
  (aulas 03, 05, 06, 07 e 08), todos pelo mesmo motivo: bloco de código longo em um
  slide que já trazia `concept-cards`. Resolvido com a classe `code-compact`.
- **`fiap-zoom.js` e `fiap-print.js` foram ligados nos 13 decks.** Verificado em
  navegador: FAB presente e zoom aplicando em todos. Atenção, o `fiap-print.js`
  revela a resposta dos quizzes em modo print.
- **`aulas-1sem/generate_classes.py` foi removido.** Era a armadilha que sobrescrevia
  os decks 02, 03, 05, 06, 07 e 08. Recuperável pelo histórico do git; substituído
  por `tools/scaffold_labs.py`.
- **`PLANO_DE_ENSINO.md` e `PLANEJAMENTO_AULA_A_AULA.md` alinhados com a ADR-002.**
  Corrigida de passagem a sobreposição de horário na agenda da Aula 02, que tinha
  dois blocos começando às 21h20.
- **O Wireshark foi removido de todo o acervo**, por decisão do professor. Saiu da
  ementa, da matriz de rastreabilidade, do `SKILL.md` e do `scaffold_labs.py`. A
  matriz afirmava que nenhum conteúdo original havia sido removido; passou a
  registrar essa exceção em vez de manter a afirmação. O que resta de menção ao
  Wireshark está na ADR-002 e aqui, que são o registro da decisão.

---

## Pendências

### Do professor

- [ ] **Criar o formulário de entrega de cada aula nova** no Microsoft Forms e passar a URL, para que o slide de entrega saia com o embed no lugar do marcador pendente. Os que já existem: Aula 01 em `https://forms.cloud.microsoft/r/sy6dHWsBHJ`, Aula 02 em `https://forms.cloud.microsoft/r/ykGYKsPAj7`.
- [ ] Decidir o subdomínio da votação ao vivo (`vote.jrcf.dev` foi a sugestão).

### Técnicas

- [ ] **REGRESSÃO NAS AULAS 05 E 06.** O validador acusa, de forma reprodutível, 4 estouros e 4 colisões de título com o logo, uma delas com 18px de sobreposição real (Aula 05, slide 14). Os arquivos estão intocados desde o commit: ninguém rodou o validador depois das últimas edições daquelas aulas. Detalhe: `aula05` slides 14, 25 e 37; `aula06` slides 14, 23, 26, 41 e 47. **As Aulas 10, 11 e 12 passam nas três checagens.** Corrigir antes de 01/09, que é quando a Aula 05 é dada.
- [ ] **Aulas 14, 15 e 16 ainda são rasas.** Decks de ~345 a ~370 linhas, sem figura, quizzes genéricos. Cada uma precisa passar pelo `construtor-aulas`. **A próxima é a Aula 14** (segurança, OAuth 2.0 e JWT, 03/11).
- [ ] **Labs 14, 15 e 16 têm só o esqueleto.** Devcontainer e README funcionam; falta o conteúdo de cada laboratório.
- [ ] **Sincronizar os três repositórios do Módulo III.** `josercf/mwe-2026-2-lab10-testes-react`, `lab11-angular-rxjs` e `lab12-rag-mcp` **existem** e respondem, mas ainda têm só o esqueleto do scaffolder. O aluno que forkar hoje abre um kit que não bate com o slide. Vale o mesmo aviso da Aula 02: copiar o conteúdo sem o `resgate/`, preservar `.devcontainer/` e `ai/ask.py`.
- [ ] **Promover ao `construtor-aulas` as três armadilhas que custaram retrabalho hoje:** regra de ligadura precisa cobrir `svg text, svg tspan` além de `pre`, `code` e `.mono`; o texto do `takeaway` cabe em até duas linhas, senão o bloco dobra de altura e estoura; e título de `h2` acima de ~65 caracteres colide com o logo. As duas primeiras já estão resolvidas localmente nos decks novos; falta o padrão nascer certo.
- [ ] **Criar os três formulários de entrega do Módulo III** no Microsoft Forms. Os slides das Aulas 10, 11 e 12 estão com marcador visível no lugar do iframe.
- [ ] **Cadastrar as nove perguntas do Módulo III no Pulso** (`aula10-quiz1|2|3`, `aula11-...`, `aula12-...`). O placeholder de QR continua no markup como fallback.
- [ ] **Cronometrar os três laboratórios do Módulo III na primeira aplicação.** Nenhum foi medido com turma. A ordem de corte de cada um está declarada no README, e a da Aula 12 é a mais apertada, porque são seis passos em 53 minutos.
- [ ] Cosmético, mas rastro de manutenção: os comentários HTML de navegação interna do `aula12.html` ficaram fora de sincronia com a posição real a partir do slide 12, resultado da inserção do slide 22 em duas etapas. Não afeta nada renderizado.
- [ ] **Criar os quatro formulários de entrega do Módulo II** no Microsoft Forms. Os slides das Aulas 05 a 08 estão com marcador visível no lugar do iframe, à espera da URL.
- [ ] **Promover ao `fiap-theme.css`** as regras que hoje vivem locais nos decks 06 e 08: desligar as ligaduras da JetBrains Mono e impedir que o `text-transform` do tema suba caminho de arquivo para maiúscula. Vale para os treze decks; revalidar todos depois.
- [ ] **Cronometrar os laboratórios do Módulo II na primeira aplicação.** Nenhum foi medido com turma; a ordem de corte de cada um está declarada no README.
- [ ] **Validar com o professor a minutagem nova da Aula 03.** A revisão moveu os Quizzes 2 e 3 para depois dos Ciclos 4 e 5 (o planejamento antigo dava toda a teoria antes do Quiz 1). Deck, planejamento e plano de ensino já estão alinhados entre si; falta o aceite explícito.
- [ ] **Avisar a turma antes de 18/08:** conta no Docker Hub criada e verificada por e-mail é pré-requisito da Aula 03 (a etapa 7 publica imagem, e a verificação custa 5 a 10 minutos).
- [ ] **Cronometrar os sete ciclos da Aula 03 na primeira aplicação.** Ordem de corte registrada no spec: primeiro o Ciclo 6 vira demonstração, depois a segunda metade do Ciclo 5; o Ciclo 7 e as Agent Skills nunca saem.
- [ ] **Decidir o destino do `gabarito/`.** Agora são dois arquivos, `server.js` e `server_telemetry.py`, commitados em `labs/aula02-lab/gabarito/`, e o workflow publica o repositório inteiro no GitHub Pages: um aluno que navegue pelo acervo acha as duas respostas. Confirmado que o repositório que o aluno forka **não** leva o gabarito, então o risco é só de quem procura no acervo. Avaliar se o gabarito sai do repositório público ou se fica assumido. A ADR-003 lista isto como risco aberto.
- [ ] **Cronometrar o lab da Aula 02 na primeira aplicação.** São 64 minutos previstos para os ~75 do Bloco 2, ou seja cerca de 11 de margem. Se faltar, o corte previsto na ADR-003 é a segunda metade do Passo 4, que são medições independentes, e nunca o Passo 5.
- [ ] **Os outros 12 repositórios de lab provavelmente estão como o da Aula 02 estava:** só o esqueleto do scaffolder, com README genérico. Ao construir cada aula, sincronizar o repositório correspondente junto, senão o aluno abre um kit que não bate com o slide.
- [ ] **A passagem por arquivo entre o coletor e o gateway precisa ser desfeita na Aula 07.** Está declarada como simplificação deliberada na ADR-002, no README do lab e no slide do Passo 2, com a Aula 07 nomeada como ponto de substituição. Ao construir a Aula 07, cobrar essa dívida.
- [ ] Duplicação no `home01`: `~/infra/docker-compose.yml` e `~/homelab/docker-compose.yml` **definem os dois o nginx-proxy-manager e o n8n**. Parece migração inacabada. Resolver antes de subir serviço novo, senão um `compose up` pode derrubar o proxy no meio de uma aula.

---

## Convenções que já custaram retrabalho

Estão no `CLAUDE.md` e no agente construtor, mas repetindo o essencial:

- Sem emojis. Português com acentuação. Nunca travessão em dash.
- Nunca expor peso de avaliação nem fórmula de nota nos slides.
- Não inventar conteúdo institucional: perguntar.
- Conceito visual pede figura, não dois cards de texto.
- Preferir SVG inline a imagem de terceiro, que é risco de licença em site público.
- **`scrollHeight` da `section` não detecta estouro**, porque a altura é fixa em 720. Use o validador.
- Nunca afirmar que validou sem ter validado.
