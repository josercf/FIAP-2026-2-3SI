# Módulo II (Aulas 05 a 08): desenho das quatro aulas

Complementa a `ADR-006`, que fixa o contrato da plataforma. Aqui está o que cada
aula ensina, entrega e verifica. Quem for construir uma aula lê **esta seção
inteira mais a da sua aula**, e segue `.claude/agents/construtor-aulas.md` para
o resto.

## 1. O que vale para as quatro

- **Formato canônico**, não o progressivo da Aula 03: a agenda minuto a minuto de
  cada aula já está no `PLANEJAMENTO_AULA_A_AULA.md` e é fonte da verdade.
  Resgate da espiral, desafio do Mini Mundo, teoria, Quiz 1, intervalo, Quizzes 2
  e 3, laboratório em passos, entrega, referências, copyright.
- **Enunciados dos três quizzes vêm prontos** do `PLANEJAMENTO_AULA_A_AULA.md`.
  Não reescreva o sentido; escreva as quatro alternativas e as duas mensagens de
  feedback. Cada quiz precisa vir **depois** do conteúdo que cobra.
- **Deck entre 50 e 55 slides, com no mínimo 8 animações SVG inline.** A régua é
  a Aula 03, e ela é explícita: profundidade equivalente, não aproximada.
  Um conceito por slide. **Todo conceito espacial, temporal, comparativo ou
  sequencial vira figura**, nunca dois cards de texto: essa substituição já
  recebeu o veredito "profundidade de um pires" em revisão anterior. Cada
  animação leva `<figcaption>` descrevendo a sequência completa, porque no PDF
  ela congela num quadro qualquer.
- **Número afirmado é número medido.** Se o deck ou o README citar tamanho,
  tempo, consumo de memória ou taxa de acerto, meça antes e registre o valor
  real. A Aula 03 mediu os quatro tamanhos de imagem antes de escrever o slide
  que os cita, e declarou a arquitetura em que mediu.
- **Validado é validado de verdade.** Rodar o serviço, subir o container,
  executar o teste, ver a falha acontecer antes da correção. Onde não for
  possível validar no ambiente, dizer isso no relatório em vez de afirmar que
  validou. A Aula 03 registrou em ADR até o que o verificador **não** consegue
  provar por máquina, e a régua é essa.
- **Votação ao vivo:** `data-quiz-key="aulaNN-quizN"` em cada quiz e
  `<script defer src="https://vote.jrcf.dev/client.js"></script>` antes de
  `</body>`.
- **Formulário de entrega ainda não existe** para nenhuma aula deste módulo. O
  slide de entrega mantém o layout, troca o `<iframe>` por um marcador visível
  dizendo que a URL será publicada antes da aula, e a pendência entra no
  relatório final. Não invente URL nem reaproveite a de outra aula.
- **Lab kit** em `aulas-1sem/labs/aulaNN-lab/`, com:
  - `servicos/` com os serviços das aulas anteriores congelados, com aviso de
    que não são tarefa;
  - o esqueleto do que o aluno completa, com lacunas nomeadas `TODO-N`;
  - `verificar.py` sem dependências, com `--criterio N` e placar, saindo 0 quando
    tudo passa e 1 quando falha, validado **nos dois sentidos** (reprova o
    esqueleto, aprova o gabarito);
  - `docs/EVIDENCIAS.md` como formulário, com marcadores que o verificador lê;
  - `README.md` com missão no case, pré-requisitos, passos, critérios de
    aceitação em tabela e como entregar. Sem peso de avaliação.
- **Entregáveis com número.** Nada de "implemente bem": diga quantas lacunas,
  quantos testes, qual valor numérico.
- **Pirâmide de testes** é pilar da disciplina: todo lab do módulo entrega testes
  de unidade rodando (JUnit, xUnit, pytest ou Vitest, conforme a stack).
- Cada laboratório cabe em **60 minutos** para quem acompanhou as aulas
  anteriores. Ordem de corte declarada no README, como na Aula 03.

## 2. Aula 05, 01/09: POO, SOLID e Design Patterns em Java e C#

**Dor de negócio:** a LogiTech vai cobrar pelos fretes que já sabe calcular, e o
contexto de Pedidos precisa gravar pedido e emitir fatura sem que a regra de
negócio fique presa ao banco nem ao meio de pagamento de cada cliente.

**Teoria:** os quatro pilares de POO com exemplo do case; os cinco princípios
SOLID, um slide cada, com o cheiro do código que viola e a versão corrigida;
Factory Method, Repository e Singleton, cada um com o problema que resolve.

Enquadramento que amarra tudo: **SOLID é o porquê, os padrões são o como.** O
DIP explica por que o Repository existe; o OCP explica por que a Factory existe.

**Laboratório.** Os dois serviços vêm compilando, rodando e com teste de unidade
passando. O aluno preenche seis lacunas:

| Lacuna | Serviço | O que exercita |
|---|---|---|
| `TODO-1` | pedidos (Java) | Extrair a interface `PedidoRepository` e fazer `PedidoService` depender dela, não de `JpaPedidoRepository` (DIP) |
| `TODO-2` | pedidos (Java) | `ConectorFaturamentoFactory` escolhendo o conector por tipo de cliente (Factory Method) |
| `TODO-3` | pedidos (Java) | Fechar `PedidoService` para modificação ao acrescentar um tipo novo de cliente (OCP), sem tocar no método existente |
| `TODO-4` | faturamento (C#) | `IFaturaRepository` com implementação EF Core e injeção por construtor |
| `TODO-5` | faturamento (C#) | `NumeradorNotaFiscal` como Singleton **thread-safe** |
| `TODO-6` | faturamento (C#) | Teste xUnit que dispara 100 emissões concorrentes e prova que não há número duplicado |

A lacuna 5 é o coração da aula: o esqueleto entrega um Singleton **sem
sincronização**, e o teste da lacuna 6 falha de verdade, com número de nota
fiscal repetido. O aluno vê a race condition acontecer antes de corrigir. É a
resposta da pergunta de verificação 3, provada em vez de afirmada.

**Entregáveis com número:** as 6 lacunas; `mvn test` e `dotnet test` verdes;
`docs/EVIDENCIAS.md` com `NOTAS_DUPLICADAS_ANTES` (maior que zero) e
`NOTAS_DUPLICADAS_DEPOIS` (igual a zero); os dois serviços respondendo em
`/health`; um `POST /api/v1/pedidos` seguido de `GET /api/v1/faturas/{id}`
funcionando ponta a ponta.

**Ambiente:** devcontainer com Java 21 e .NET 8. O PostgreSQL sobe por
`docker run` com a rede `logitech-net`, reaproveitando o que a Aula 03 ensinou.
Na Aula 07 esse mesmo banco vira serviço do Compose: o aluno precisa reconhecer
o comando dele virando três linhas de YAML.

## 3. Aula 06, 08/09: Adapter, Decorator e Strategy em Node e Python

**Dor de negócio:** o frete tem regras diferentes por modalidade e muda por
campanha comercial; as notificações precisam de log e reenvio sem que a regra de
envio seja reescrita; e o rastreamento da transportadora parceira responde num
formato legado que ninguém controla.

**Teoria:** Strategy, Adapter e Decorator, um bloco cada, sempre com o antes
(cadeia de `if` e acoplamento à API alheia) e o depois; `async`/`await` e o event
loop comparado ao modelo síncrono de Java e C# da aula anterior; contrato de API
com Pydantic e Zod gerando OpenAPI.

**Laboratório.** Seis lacunas:

| Lacuna | Serviço | O que exercita |
|---|---|---|
| `TODO-1` | frete (FastAPI) | `EstrategiaFrete` como protocolo comum |
| `TODO-2` | frete | `FreteExpresso` e `FreteEconomico` como estratégias |
| `TODO-3` | frete | Registro de estratégias, para acrescentar modalidade sem tocar na rota (OCP) |
| `TODO-4` | notificacoes (Node TS) | `AdaptadorRastreioLegado` traduzindo o formato da parceira para o do case |
| `TODO-5` | notificacoes | `ComLog` como Decorator do enviador |
| `TODO-6` | notificacoes | `ComRetentativa` como segundo Decorator, empilhável ao primeiro |

A prova de que Decorator empilha: o teste envia por um canal que falha uma vez e
confirma, no log, a tentativa, a falha, a nova tentativa e o sucesso, **sem que a
classe do enviador tenha sido alterada**.

**Entregáveis com número:** as 6 lacunas; `pytest` e `vitest` verdes; uma
modalidade nova de frete acrescentada **sem modificar** a rota, provada por
`git diff` citado em `docs/EVIDENCIAS.md`; `VALOR_EXPRESSO_500KM` e
`VALOR_ECONOMICO_500KM` registrados; `/docs` do FastAPI e o schema Zod
respondendo.

## 4. Aula 07, 15/09: Docker Compose multi-serviço e AI Gateway

**Dor de negócio:** a plataforma agora tem seis serviços e um banco, e subir isso
à mão é uma sequência de comandos que ninguém reproduz igual duas vezes. E cada
serviço que quiser usar IA não pode ter a sua própria integração com provedor.

**Teoria:** anatomia do `docker-compose.yml`; `depends_on` com
`condition: service_healthy` e por que `depends_on` sozinho não basta (é a
pergunta de verificação 1, e merece animação mostrando o serviço subindo antes de
o banco aceitar conexão); rede e DNS entre serviços, retomando a Aula 03;
variáveis, `env_file` e o que nunca entra no arquivo; volumes nomeados; limites
de memória por serviço. Depois, arquitetura de AI Gateway: Facade escondendo os
provedores, Strategy escolhendo entre eles, fallback, rate limit e caching
semântico.

**Laboratório em cinco passos**, cada um subindo o que já escreveu:

1. `postgres` com `healthcheck`, mais `pedidos` com
   `depends_on: condition: service_healthy`. O passo 1 pede que o aluno rode
   **primeiro sem** o `healthcheck` e veja o serviço quebrar na largada.
2. `faturamento`, `frete` e `notificacoes`, com rede, variáveis e limites de
   memória.
3. `coletor` e `painel`, **pagando a dívida da ADR-002**: o painel deixa de ler
   o arquivo compartilhado e passa a consumir `GET /telemetria` na 8082 do
   coletor, por variável `LOGITECH_TELEMETRIA_URL`.
4. `ai-gateway`, com os dois provedores atrás da fachada e o fallback
   acontecendo de verdade.
5. `docker compose up -d` com os oito de pé, `docker compose ps` mostrando todos
   saudáveis, e um pedido percorrendo a plataforma inteira.

**Entregáveis com número:** `docker-compose.yml` com os 8 serviços; `compose ps`
com 8 `healthy`; `TEMPO_ATE_TODOS_SAUDAVEIS_S`; `MEMORIA_TOTAL_MB`;
`FALLBACK_ACIONADO` com o trecho de log; `ACERTOS_DE_CACHE` depois de repetir a
mesma pergunta três vezes; e a evidência de que o painel não lê mais arquivo.

**Aviso obrigatório no roteiro:** parar o Ollama antes do `compose up` no
Codespace, por memória, e o que esperar do gateway nesse cenário.

## 5. Aula 08, 22/09: Function Calling, Command Pattern e Git Worktrees

**Dor de negócio:** o atendimento da LogiTech responde à mão a duas perguntas o
dia inteiro, "onde está meu pedido" e "muda o endereço de entrega". O agente
pode resolver, desde que **não** ganhe acesso solto ao banco.

**Teoria:** o que é Function Calling e por que a saída do modelo é intenção, não
comando; JSON Schema como contrato, com validação antes da execução; Command
Pattern dando autorização, auditoria e desfazimento; o que jamais vira
ferramenta. Depois, Git Worktrees: por que `git checkout` quebra com dois agentes
no mesmo repositório (pergunta de verificação 1, com animação de dois agentes
disputando o mesmo diretório de trabalho), `git worktree add`, `list` e `remove`.

**Laboratório.** O agente vem com o laço de conversa pronto e duas ferramentas
declaradas. Cinco lacunas:

| Lacuna | O que exercita |
|---|---|
| `TODO-1` | JSON Schema de `consultar_status_pedido` |
| `TODO-2` | JSON Schema de `alterar_endereco_entrega`, com os campos obrigatórios |
| `TODO-3` | `ConsultarStatusPedido` como Command, chamando `GET /api/v1/pedidos/{id}/status` |
| `TODO-4` | `AlterarEnderecoEntrega` como Command, com validação **antes** do `PATCH` e registro em `docs/AUDITORIA.md` |
| `TODO-5` | Recusa auditada: comando que não passa no schema não executa e é registrado |

A lacuna 5 é o critério que separa integração de engenharia: o roteiro manda
provocar o agente a alterar endereço **sem informar o CEP**, e o esperado é
recusa registrada, não uma chamada malformada indo ao banco.

Modo `--simular` injeta uma resposta de LLM já formada, para que Command,
auditoria e worktrees continuem exercitáveis se o modelo local falhar no tool
calling. Isso é declarado ao aluno, não escondido.

**Worktrees:** criar `../wt-agente-pedidos` e `../wt-agente-atendimento` a partir
de duas branches, rodar o agente nas duas ao mesmo tempo e provar, com
`git worktree list` e com os dois processos vivos, que não houve conflito.

**Entregáveis com número:** as 5 lacunas; `pytest` verde; `docs/AUDITORIA.md` com
no mínimo 3 execuções autorizadas e 1 recusa; `git worktree list` com as duas
worktrees; `PEDIDO_ALTERADO_ID` e `MOTIVO_DA_RECUSA` em `docs/EVIDENCIAS.md`.

## 6. O que este spec deliberadamente não decide

- **Enunciado dos quizzes:** já fixado no planejamento, não se reabre.
- **Datas e títulos:** vêm do `PLANO_DE_ENSINO.md`.
- **URL dos formulários:** não existe ainda; o professor publica depois.
- **Peso de avaliação:** não entra em slide nem em README, por convenção do acervo.

## 7. Riscos abertos do módulo

| Risco | Onde vigiar |
|---|---|
| A Aula 07 depende de seis serviços funcionando; um deles quebrado inviabiliza o lab inteiro | Os serviços vão congelados no lab kit, e o verificador da Aula 07 checa `/health` de cada um antes de julgar o Compose |
| Codespace de 2 núcleos com Java, .NET e Postgres juntos | Medir na primeira aplicação e registrar; limites de memória já no Compose |
| Tool calling do modelo local | Modo `--simular` e critério de aceitação que não depende do acerto do modelo |
| Quatro aulas construídas em paralelo divergirem | Contrato da ADR-006, e uma passada de conferência cruzada antes de publicar |
