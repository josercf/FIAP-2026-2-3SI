# Módulo IV (Aulas 14 a 16): desenho das três aulas

Complementa a `ADR-009`, que fixa o contrato de segurança. Quem for construir
uma aula lê **a seção 1 mais a da sua aula**, e segue
`.claude/agents/construtor-aulas.md` para o resto.

## 1. O que vale para as três

Vale tudo o que valeu no Módulo II e no III, com a régua da Aula 03:

- **Deck de 50 a 55 slides, no mínimo 8 animações SVG inline**, cada uma com
  `<figcaption>` descrevendo a sequência completa. Conceito espacial, temporal,
  comparativo ou sequencial vira **figura**, nunca dois cards de texto.
- **Número afirmado é número medido.** Tempo, contagem de CVE, latência: mede,
  registra o ambiente e a data.
- **Validado quer dizer executado.** Ver o ataque funcionar antes da defesa, ver
  o 401 e o 403 acontecerem, ver o Trivy apontar CVE de verdade.
- **Formato canônico**, agenda minuto a minuto do `PLANEJAMENTO_AULA_A_AULA.md`.
  A Aula 16 é a exceção e está descrita na seção 4.
- **Quizzes** com os enunciados do planejamento, sem reescrever o sentido, e
  cada um **depois** do conteúdo que cobra. `data-quiz-key="aulaNN-quizN"` e o
  `client.js` do Pulso.
- **Formulário de entrega não existe** para nenhuma aula deste módulo: marcador
  visível no lugar do iframe, pendência no relatório final.
- **Lab kit** com `servicos/` congelados, lacunas `TODO-N`, `verificar.py` sem
  dependências validado nos dois sentidos, `docs/EVIDENCIAS.md` com marcadores,
  README com critérios em tabela e ordem de corte. Sem peso de avaliação.
- **Testes de unidade** rodando, conforme a stack de cada lab.
- Cada laboratório cabe em **60 minutos** para quem acompanhou o semestre.

### O interruptor que não pode ser esquecido

A `ADR-009` criou `LOGITECH_AUTH_ATIVA`, padrão `false`. Os laboratórios das
Aulas 05 a 12 já estão publicados e continuam passando com ela desligada. Quem
construir a Aula 14 **liga no Compose dela**, e o verificador exige ligada.
Quem construir as Aulas 15 e 16 assume ligada.

## 2. Aula 14, 03/11: OAuth 2.0, OIDC, JWT, RBAC e Git Worktrees II

**Dor de negócio:** hoje qualquer um que alcance a rede da LogiTech altera o
endereço de entrega de qualquer pedido. O `PATCH /api/v1/pedidos/{id}/endereco`
que o agente da Aula 08 chama não pergunta quem está chamando.

**Teoria:** o problema que OAuth resolve e por que senha compartilhada entre
serviços não é resposta; Authorization Code com **PKCE**, passo a passo, e por
que SPA não guarda segredo; anatomia do JWT (header, payload, assinatura) com
um token real decodificado na tela; JWKS e por que o backend não consulta banco
a cada requisição; RBAC com papel em `realm_access.roles`; 401 contra 403.
Depois, Git Worktrees II: `/worktrees/agent-auth` e `/worktrees/agent-ui`
rodando refatoração em paralelo, retomando a Aula 08.

Animações que a aula pede: o fluxo PKCE inteiro, do clique ao token; a
assinatura sendo conferida contra o JWKS; o mesmo token batendo em 200, 401 e
403 conforme o papel.

**Laboratório.** Seis lacunas:

| Lacuna | Onde | O que exercita |
|---|---|---|
| `TODO-1` | Compose | Serviço `keycloak` com `--import-realm` e healthcheck |
| `TODO-2` | `pedidos` (Java) | Filtro que valida o JWT pelo JWKS e devolve 401 |
| `TODO-3` | `pedidos` | RBAC nas rotas do contrato, devolvendo 403 sem o papel |
| `TODO-4` | `frete` ou `notificacoes` | O mesmo em outra stack, provando que o papel vem do mesmo lugar |
| `TODO-5` | Portal React | Login por PKCE e envio do `Authorization: Bearer` |
| `TODO-6` | Worktrees | Duas worktrees com o trabalho de segurança separado do de interface |

**Entregáveis com número:** as 6 lacunas; `curl` sem token devolvendo **401** e
com token de papel errado devolvendo **403**, os dois registrados;
`TOKEN_EXPIRA_EM_S` lido do próprio token; `PAPEIS_NO_TOKEN` copiado de
`realm_access.roles`; `git worktree list` com as duas worktrees; testes verdes.

**Armadilha a transformar em conteúdo:** o `issuer` visto de dentro da rede
(`keycloak:8090`) e do navegador (`localhost:8090`) não coincidem, e a
validação falha com mensagem ruim. Está na `ADR-009` e precisa virar slide.

## 3. Aula 15, 10/11: OWASP Top 10 para LLM e Trivy

**Dor de negócio:** o assistente da LogiTech responde a cliente e tem ferramenta
que altera pedido. Um texto bem escrito dentro da pergunta pode fazer o modelo
ignorar a instrução de sistema. E as imagens que sobem em produção carregam
pacote com CVE conhecida desde a Aula 03.

**Teoria:** OWASP Top 10 para LLM, com foco em Prompt Injection direto e
indireto, Insecure Output Handling e Sensitive Information Disclosure; o
paralelo com SQL Injection, que é a analogia da pergunta de verificação 1;
guardrails de entrada e de saída e por que filtro de palavra proibida não
resolve; mascaramento de dado sensível; depois, cadeia de suprimentos: o que o
Trivy lê, o que é CVE, severidade, `--ignore-unfixed` e por que aceitar HIGH
com justificativa escrita é diferente de esconder.

Animações que a aula pede: a instrução do usuário sobrescrevendo a de sistema;
a injeção **indireta** chegando por um documento que o RAG recuperou, que é o
elo com a Aula 12; a camada de guardrail interceptando entrada e saída; as
camadas da imagem sendo varridas e a CVE acendendo numa delas.

**Laboratório.** Seis lacunas:

| Lacuna | Onde | O que exercita |
|---|---|---|
| `TODO-1` | ai-gateway | Detector de sobrescrita de instrução, recusando com 422 |
| `TODO-2` | ai-gateway | Mascaramento de CPF, cartão e placa na saída |
| `TODO-3` | ai-gateway | Contadores `guardrail.*` na rota de métricas |
| `TODO-4` | rag | Sanitizar o trecho recuperado antes de compor o prompt (injeção indireta) |
| `TODO-5` | Dockerfile | Corrigir o que o Trivy apontou como CRITICAL |
| `TODO-6` | `docs/EXCECOES.md` | Registrar HIGH aceito, com data e motivo |

O roteiro **manda desligar o guardrail primeiro** e executar a injeção com
sucesso, registrando a resposta que o modelo deu. Só depois liga. E, na lacuna
1, exige que o aluno tente **quebrar o próprio filtro** e registre uma
formulação que passou: filtro que ninguém tentou furar não é defesa.

**Entregáveis com número:** as 6 lacunas; `INJECAO_ANTES` e `INJECAO_DEPOIS`;
`CVES_CRITICAL_ANTES` e `CVES_CRITICAL_DEPOIS` (zero); `CVES_HIGH_ACEITAS` com
o arquivo de exceções; `FORMULACAO_QUE_PASSOU` no relato do aluno; testes verdes.

## 4. Aula 16, 17/11: integração end-to-end e simulado da Global Solution

**Esta aula tem formato próprio** e o `PLANEJAMENTO_AULA_A_AULA.md` a descreve
como hackathon: não há bloco de teoria novo, e o encontro é Bloco 1 de
integração, intervalo, Bloco 2 de simulado da banca, e orientações finais.

Consequências para o deck, que **não** segue a ordem canônica inteira:

- Sem os três quizzes de conteúdo novo. No lugar, o **checklist da GS** em três
  perguntas de verificação funcional, que o planejamento já dá: sobe tudo com um
  comando, a autenticação protege backend e frontend, e o AI Gateway com o MCP
  respondem. Elas viram slides de verificação com o mesmo markup de quiz, com
  `data-quiz-key="aula16-checkN"`, porque a votação ao vivo continua útil aqui.
- O miolo é **runbook e diagnóstico**: mapa da plataforma inteira com os treze
  serviços, ordem de subida, o que olhar quando cada um falha, e os erros que já
  aconteceram no semestre (healthcheck com `localhost` resolvendo IPv6, issuer
  divergente, rede e volume `external` faltando, porta ocupada).
- Um slide por **fluxo de integração** a validar, do clique no portal até o
  banco, atravessando token, gateway e RAG.
- Slides finais sobre a banca: o que a apresentação precisa mostrar, em que
  ordem, e o que costuma dar errado ao vivo.

**Laboratório**, que aqui é o hackathon guiado, com cinco frentes verificáveis:

| Frente | Critério |
|---|---|
| 1 | `docker compose up -d --wait` com os treze serviços saudáveis |
| 2 | Fluxo autenticado ponta a ponta: login no portal, pedido criado, fatura emitida |
| 3 | Guardrail ativo e injeção recusada, com o registro |
| 4 | RAG respondendo com fonte citada e o MCP servindo a ferramenta |
| 5 | Trivy sem CRITICAL nas imagens do projeto |

**Entregáveis com número:** os cinco critérios verdes; `TEMPO_ATE_TODOS_SAUDAVEIS_S`
e `MEMORIA_TOTAL_MB` medidos na máquina do grupo; um roteiro de apresentação de
**10 minutos** escrito, com quem fala o quê; e o repositório com README que sobe
a plataforma do zero.

O `verificar.py` desta aula é o mais completo do semestre e serve de
**autoavaliação para a banca**: é o mesmo que o professor roda.

## 5. O que este spec deliberadamente não decide

- **Enunciados dos quizzes das Aulas 14 e 15:** já estão no planejamento.
- **Datas e títulos:** vêm do `PLANO_DE_ENSINO.md`.
- **URL dos formulários:** não existem ainda.
- **Aula 17 (08/12), feedback da GS e roadmap:** fica **fora** deste módulo.
  É retrospectiva do semestre e depende do resultado real da banca e da leitura
  do professor sobre a turma. Construir agora seria inventar conteúdo
  institucional, o que as convenções do acervo proíbem.
- **Peso de avaliação:** não entra em slide nem em README.

## 6. Riscos abertos do módulo

| Risco | Onde vigiar |
|---|---|
| Treze serviços na Aula 16 não caberem na máquina do aluno | Medir e registrar; subir por grupos se necessário, com o número declarado |
| O aluno colar o `curl` com token sem entender o fluxo | A Aula 14 obriga o PKCE pelo navegador antes de qualquer `curl` |
| O resultado do Trivy mudar com o tempo | Critério é "zero CRITICAL", não um total fixo, e o slide leva a data da varredura |
| A Aula 16 depender de doze laboratórios alheios | O kit traz a plataforma congelada |
| O guardrail virar teatro | O laboratório exige que o aluno fure o próprio filtro e registre |
