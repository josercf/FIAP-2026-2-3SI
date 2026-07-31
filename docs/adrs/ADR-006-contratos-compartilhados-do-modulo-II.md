# ADR-006: Contratos compartilhados da plataforma no Módulo II

- **Data:** 2026-07-31
- **Status:** Aceita
- **Decisores:** Prof. José Romualdo da Costa Filho

## Contexto

O Módulo II tem quatro aulas que, pela primeira vez no semestre, **não são
independentes entre si**:

- Aula 05 (01/09) constrói Pedidos em Java e Faturamento em C#.
- Aula 06 (08/09) constrói Frete em Python e Notificações em Node.
- Aula 07 (15/09) **orquestra os quatro com Docker Compose** e acrescenta o AI Gateway.
- Aula 08 (22/09) põe um **agente de IA chamando a API de Pedidos** por Function Calling.

Se cada laboratório for construído isoladamente, a Aula 07 não tem o que
orquestrar: nomes de serviço, portas, rotas e variáveis de ambiente não vão
casar, e a Aula 08 não sabe em que endereço bater. Nas Aulas 01 a 03 esse risco
não existia, porque cada aula evoluía um único par de serviços.

Existe ainda uma **dívida declarada**: a ADR-002 e o slide de encerramento da
Aula 03 prometem que a passagem por arquivo entre o coletor e o painel de
telemetria é substituída na Aula 07.

## Decisão

Fixar, antes de escrever qualquer aula do módulo, o **contrato da plataforma
LogiTech**: nomes de serviço, portas, rotas, banco, rede e variáveis de
ambiente. Todo laboratório do módulo entrega e consome exatamente esses nomes.

### Serviços e portas

| Serviço | Container | Linguagem | Porta | Nasce na | Bounded Context |
|---|---|---|---|---|---|
| Coletor de telemetria | `coletor` | Python | 8081/udp e 8082/tcp | Aula 02 | Telemetria |
| Painel de rastreamento | `painel` | Node | 3000 | Aula 02 | Telemetria |
| Pedidos | `pedidos` | Java 21, Spring Boot 3 | 8080 | Aula 05 | Pedidos |
| Faturamento | `faturamento` | C#, .NET 8 | 5080 | Aula 05 | Faturamento |
| Cálculo de frete | `frete` | Python, FastAPI | 8000 | Aula 06 | Pedidos (apoio) |
| Notificações | `notificacoes` | Node 22, TypeScript | 3001 | Aula 06 | Atendimento |
| Banco | `postgres` | PostgreSQL 16 | 5432 | Aula 07 | infraestrutura |
| AI Gateway | `ai-gateway` | Python, FastAPI | 4000 | Aula 07 | infraestrutura |

A porta **8082/tcp no coletor é nova** e existe para pagar a dívida da ADR-002:
é por ela que o painel passa a ler a telemetria, em vez de ler o arquivo
compartilhado.

### Rotas que outros serviços consomem

Rota que ninguém de fora chama não entra neste contrato; o que está aqui é o
que outra aula depende.

```
pedidos        GET   /health
               GET   /api/v1/pedidos
               GET   /api/v1/pedidos/{id}
               POST  /api/v1/pedidos
               PATCH /api/v1/pedidos/{id}/endereco     <- usado pelo agente da Aula 08
               GET   /api/v1/pedidos/{id}/status       <- usado pelo agente da Aula 08

faturamento    GET   /health
               POST  /api/v1/faturas
               GET   /api/v1/faturas/{pedidoId}

frete          GET   /health
               POST  /api/v1/frete/cotacao
                     entra {origem, destino, pesoKg, modalidade}
                     sai   {valor, prazoDias, modalidade}

notificacoes   GET   /health
               POST  /api/v1/notificacoes
                     entra {canal, destinatario, mensagem}

ai-gateway     GET   /health
               POST  /v1/chat/completions              <- formato compatível com OpenAI
               GET   /v1/metricas                      <- acertos de cache, uso por provedor

coletor        GET   /telemetria                       <- porta 8082, paga a dívida da ADR-002
painel         GET   /health, GET /, GET /api/v1/posicoes, GET /api/v1/eventos
```

Todo serviço expõe `GET /health` devolvendo `200` e `{"status":"ok"}`. Sem isso
o `healthcheck` do Compose na Aula 07 não tem em que se apoiar.

### Banco, rede e volumes

- PostgreSQL 16, banco `logitech`, usuário `logitech`, senha por variável.
- Um schema por Bounded Context: `pedidos` e `faturamento`. Nenhum serviço lê a
  tabela do outro: quem precisa de dado alheio chama a API.
- Rede `logitech-net`, a **mesma criada à mão na Aula 03**.
- Volumes `logitech-postgres` (dados do banco) e `logitech-telemetria` (herdado
  da Aula 03).

### Variáveis de ambiente

Prefixo `LOGITECH_`, seguindo o `LOGITECH_DADOS` da Aula 03:

```
LOGITECH_DB_URL, LOGITECH_DB_USER, LOGITECH_DB_PASSWORD
LOGITECH_PEDIDOS_URL, LOGITECH_FATURAMENTO_URL
LOGITECH_FRETE_URL, LOGITECH_NOTIFICACOES_URL
LOGITECH_AI_GATEWAY_URL
LOGITECH_TELEMETRIA_URL
```

A `LOGITECH_FATURAMENTO_URL` entrou depois, em 31/07/2026: a construção da
Aula 05 mostrou que Pedidos chama Faturamento para emitir a fatura, e essa
aresta tinha ficado de fora da primeira versão desta ADR. Quem consome:
o serviço `pedidos` na Aula 05 e o Compose da Aula 07.

Endereço de serviço **nunca** aparece cravado no código: vem de variável, com
padrão de desenvolvimento local. É o que permite o mesmo código rodar solto na
máquina do aluno e dentro do Compose.

### Cada laboratório congela o que a aula anterior entregou

Padrão que a Aula 03 estabeleceu e que passa a valer para o módulo inteiro: o
lab kit da aula N traz, em `servicos/`, os serviços das aulas anteriores
**prontos e congelados**, com aviso de que não são tarefa. Sem isso, quem faltou
a uma aula não consegue fazer a seguinte, e a Aula 07 dependeria de quatro
laboratórios alheios terem sido concluídos.

### Fallback do AI Gateway sem provedor pago

O planejamento pedia "fallback entre OpenAI e modelos locais". Não há chave de
OpenAI para a turma, e a ADR-005 tirou o GitHub Models. O gateway passa a ter
dois provedores atrás da mesma fachada:

1. `remoto`, endpoint compatível com OpenAI, configurável por variável e
   **indisponível na sala de aula**;
2. `local`, o Ollama do devcontainer.

O fallback acontece **de verdade**, e não simulado: a chamada ao remoto falha
por ausência de credencial e o gateway cai no local. O aluno vê o evento no log
e na rota de métricas. Se o professor tiver uma chave, basta preencher a
variável para o caminho remoto passar a responder, sem mexer no código.

## Motivações

- Sem contrato fixado antes, a Aula 07 vira uma aula de conserto de
  incompatibilidade, não de orquestração.
- Nomes estáveis são o que permite construir as quatro aulas em paralelo.
- Um `/health` por serviço é pré-requisito do `healthcheck` que a própria Aula 07
  ensina, e responde a pergunta de verificação sobre `depends_on`.
- Fallback real vale mais pedagogicamente do que fallback encenado, e não
  depende de cota nem de cartão de ninguém.

## Riscos conhecidos

| Risco | Mitigação |
|---|---|
| Oito containers na Aula 07 estouram a memória do Codespace | Limites `--memory` por serviço no Compose, aplicando o que a Aula 03 ensinou; o roteiro manda parar o Ollama antes do `compose up` e avisa que o AI Gateway usa o caminho remoto ou fica fora nesse momento |
| Java e C# na mesma noite é muito para 60 minutos | Os dois serviços vêm compilando e rodando; o aluno preenche lacunas nomeadas, três em cada, todas correspondendo a uma decisão de projeto |
| Tool calling do modelo local falhar na Aula 08 | O agente tem modo `--simular`, que injeta uma resposta de LLM já formada; a camada de Command e as worktrees continuam exercitáveis mesmo com o modelo errando |
| Aluno que faltou não tem o serviço da aula anterior | Cada lab kit traz os serviços anteriores congelados em `servicos/` |

## Consequências

**Positivas**
- As quatro aulas podem ser construídas em paralelo sem divergir.
- A Aula 07 tem uma plataforma real para orquestrar, e a dívida da ADR-002 é paga
  no ponto onde foi prometida.
- A Aula 08 sabe exatamente qual rota chamar, e o CP2 tem escopo verificável.

**Negativas**
- Mudar uma porta ou uma rota depois exige tocar em até quatro laboratórios e
  quatro decks. O contrato passa a ser ele próprio um artefato a versionar.
- O contrato antecipa decisões que, num projeto real, emergiriam do código.

## ADRs relacionadas

- `ADR-002` e `ADR-003`: escopo do laboratório da Aula 02, origem da dívida da
  passagem por arquivo que esta ADR agenda para a Aula 07.
- `ADR-004`: formato progressivo da Aula 03. O Módulo II **não** o adota: as
  agendas minuto a minuto das Aulas 05 a 08 já estão no
  `PLANEJAMENTO_AULA_A_AULA.md` no formato canônico, e o conteúdo delas não se
  fatia em ciclos curtos e independentes como o de Docker se fatiava.
- `ADR-005`: fim do GitHub Models, que motiva o desenho do fallback do gateway.
