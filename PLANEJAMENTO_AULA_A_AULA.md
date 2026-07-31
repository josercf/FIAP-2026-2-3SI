# Planejamento Detalhado Aula a Aula (1º Semestre - 2026-2)
## Disciplina: Microservice and Web Engineering & IT Services
**Curso:** Graduação em Sistemas de Informação (3º Ano - Turma de Agosto)  
**Instituição:** FIAP  
**Horário das Aulas:** Terças-feiras, das 19h20 às 22h50 (3,5 horas)  
**Professor:** Prof. José Romualdo da Costa Filho  
**Case Integrador:** *LogiTech Enterprise AI Platform*  

---

## Estrutura Padrão do Encontro (19h20 às 22h50)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ BLOCO 1 (19h20 – 20h50) [90 min]                                                       │
│ ├─ 19h20 - 19h35 [15 min]: Resgate da Espiral (Recap da aula anterior & conexão)        │
│ ├─ 19h35 - 19h55 [20 min]: O Desafio do Mini Mundo LogiTech (Problema de negócio)      │
│ ├─ 19h55 - 20h35 [40 min]: Fundamentação Teórica, Métodos & Padrões                    │
│ └─ 20h35 - 20h50 [15 min]: Pergunta de Verificação #1 & Espaço para Dúvidas I          │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ ☕ INTERVALO (20h50 – 21h20) [30 min] - Pausa para Café e Networking                    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ BLOCO 2 (21h20 – 22h50) [90 min]                                                       │
│ ├─ 21h20 - 21h35 [15 min]: Perguntas de Verificação #2 e #3 (Fixação dos Padrões)      │
│ ├─ 21h35 - 22h35 [60 min]: Construção Guiada & Atividade Prática (Hands-on Lab)        │
│ └─ 22h35 - 22h50 [15 min]: Espaço para Dúvidas II, Commit no Git & Entregável          │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Módulo I: Requisitos, SDLC, Redes & Conteinerização (Agosto)

### Aula 01 (04/08/2026) - SDLC, Git, Requisitos (PRD/SDD), DDD & Modelo OSI (Sockets TCP/UDP)
- **Objetivos de Aprendizagem:** Definir o PRD/SDD da plataforma *LogiTech*, mapear Bounded Contexts em DDD, configurar o repositório Git e construir um servidor de Sockets na camada L4 (TCP/UDP) em Python.
- **Espiral Pedagógica:** Nivelamento inicial de Engenharia de Software e Redes.
- **Desafio do Mini Mundo:** A *LogiTech* possui uma frota de caminhões que emite telemetria via sensores IoT. Precisamos capturar esse fluxo bruto na camada de transporte.
- **Agenda em Minutos:**
  - `19h20 - 19h35`: Apresentação da disciplina, contrato pedagógico e visão geral do ano letivo.
  - `19h35 - 19h55`: Apresentação do Case *LogiTech Enterprise* e introdução ao PRD/SDD e DDD (Bounded Contexts).
  - `19h55 - 20h35`: Teoria: Modelo OSI (L1-L7), Camada de Transporte: TCP (3-way handshake) vs UDP (datagramas).
  - `20h35 - 20h50`: **Pergunta de Verificação #1** + Tira-dúvidas do Bloco 1.
  - `20h50 - 21h20`: ☕ **INTERVALO (30 min)**.
  - `21h20 - 21h35`: **Perguntas de Verificação #2 e #3**.
  - `21h35 - 22h35`: **Atividade Prática em Dupla:** Inicializar o Git do grupo, escrever o PRD/SDD em Markdown e programar um servidor de Socket TCP/UDP em Python na porta 8080.
  - `22h35 - 22h50`: Espaço para Dúvidas II + Push do código no repositório Git.
- **Sessão de Perguntas de Verificação:**
  1. *Pergunta 1:* Qual a diferença fundamental entre TCP e UDP e por que a telemetria de velocidade do caminhão pode usar UDP, mas a confirmação da entrega exige TCP?  
     *Resposta Esperada:* TCP é orientado a conexão e garante a entrega dos pacotes na ordem correta (ideal para contratos/entregas). UDP envia datagramas sem garantia, priorizando velocidade e baixa latência (ideal para telemetria frequente onde eventuais perdas não travam a aplicação).
  2. *Pergunta 2:* O que é um Bounded Context no DDD e como ele ajuda a separar o contexto de Pedidos do contexto de Telemetria?  
     *Resposta Esperada:* É uma fronteira explícita onde um modelo de domínio se aplica. Permite que "Pedido" tenha regras e significado no contexto financeiro/logístico sem poluir a área de telemetria de sensores.
  3. *Pergunta 3:* Qual a importância da convenção de commits (Conventional Commits) no ciclo de vida de desenvolvimento de software (SDLC)?  
     *Resposta Esperada:* Padroniza o histórico de alterações (`feat:`, `fix:`, `docs:`), facilita o code review automatizado e permite geração de changelogs e versionamento semântico automatizados.
- **Entregável Prático:** Repositório Git com PRD/SDD em Markdown e arquivo `server_telemetry.py` rodando Sockets TCP/UDP.

---

### Aula 02 (11/08/2026) - Protocolos de Aplicação: HTTP/1.1 a 3, SSE, cURL & Git Workflows
- **Objetivos de Aprendizagem:** Subir do Socket L4 para a camada L7 (HTTP), comparar HTTP/1.1, HTTP/2 e HTTP/3, inspecionar tráfego com `cURL` e praticar Git Branching/Pull Requests.
- **Espiral Pedagógica:** **Recupera Aula 01** (Subindo do Socket L4 TCP da Aula 01 para a API HTTP L7, seguindo a estrutura do PRD/SDD).
- **Desafio do Mini Mundo:** Converter a telemetria capturada via Socket bruto em um serviço HTTP com streaming Server-Sent Events (SSE) para os operadores da *LogiTech*.
- **Agenda em Minutos:**
  - `19h20 - 19h35`: **Resgate da Espiral:** Conectando o Socket TCP da Aula 01 à camada de aplicação HTTP.
  - `19h35 - 19h55`: Desafio: Expor dados de Sockets para dashboards web usando HTTP/SSE.
  - `19h55 - 20h35`: Teoria: Verbos HTTP, Status Codes, Headers, HTTP/1.1 (pipelining) vs HTTP/2 (multiplexação binária) vs HTTP/3 (QUIC/UDP). TLS/SSL Handshake.
  - `20h35 - 20h50`: **Pergunta de Verificação #1** + Tira-dúvidas.
  - `20h50 - 21h20`: ☕ **INTERVALO (30 min)**.
  - `21h20 - 21h35`: **Perguntas de Verificação #2 e #3**.
  - `21h35 - 22h35`: **Atividade Prática em Dupla:** Criar uma branch `feature/http-telemetry`, completar o coletor de sockets UDP especificado no SDD, desenvolver sobre ele um servidor em Node.js exposto via HTTP/SSE, e medir o tráfego com `cURL`.
  - `22h35 - 22h50`: Abrir e aprovar Pull Request no Git com revisão cruzada entre duplas, apoiada pela skill `code-review` + Tira-dúvidas.
- **Sessão de Perguntas de Verificação:**
  1. *Pergunta 1:* Como a multiplexação no HTTP/2 resolve o problema de Head-of-Line Blocking do HTTP/1.1?  
     *Resposta Esperada:* O HTTP/2 divide as mensagens em frames binários e permite enviar múltiplas requisições/respostas simultâneas sobre uma única conexão TCP, sem que uma requisição lenta bloqueie as demais.
  2. *Pergunta 2:* Por que o protocolo Server-Sent Events (SSE) é mais simples que WebSockets para cenários de streaming unidirecional de telemetria?  
     *Resposta Esperada:* O SSE opera sobre HTTP padrão com reconexão automática nativa do navegador e menor overhead, sendo ideal para cenários onde apenas o servidor envia atualizações contínuas ao cliente.
  3. *Pergunta 3:* Qual a diferença prática entre trabalhar direto na branch `main` e utilizar um fluxo de Git Branching com Pull Requests?  
     *Resposta Esperada:* Trabalhar em branches isoladas permite desenvolver sem quebrar o ambiente estável (`main`), possibilita a revisão de código por pares e testes automatizados de integração antes do merge.
- **Entregável Prático:** Pull Request aprovado contendo o coletor UDP completado, o servidor HTTP/SSE em Node.js, três medições numéricas de tráfego em `docs/OBSERVACOES.md` e o registro da revisão feita no PR da dupla vizinha em `docs/CODE_REVIEW.md`. O escopo do laboratório está registrado nas ADRs 002 e 003.

---

### Aula 03 (18/08/2026) - Docker I: Engine, Imagens, Dockerfile Multi-Stage & Persistência
- **Objetivos de Aprendizagem:** Conteinerizar os serviços de Sockets e HTTP desenvolvidos nas aulas anteriores usando Dockerfiles Multi-Stage otimizados e gerenciamento de volumes.
- **Espiral Pedagógica:** **Recupera Aulas 01 e 02** (Empacotando os serviços Python e Node.js das Aulas 01 e 02 dentro de containers Docker).
- **Desafio do Mini Mundo:** Padronizar a execução dos serviços de telemetria da *LogiTech* para evitar inconsistências de ambiente entre desenvolvimento e produção.
- **Agenda em Minutos** (formato progressivo: sete ciclos de teoria + prática individual, um commit por etapa):
  - `19h20 - 19h40`: **Resgate da Espiral** (os serviços das Aulas 01 e 02) e **Desafio do Mini Mundo** ("na minha máquina funciona").
  - `19h40 - 20h00`: **Ciclo 1, Isolamento de processos:** chroot, namespaces, cgroups + Atividade 1.
  - `20h00 - 20h20`: **Ciclo 2, Imagem, camadas e efemeridade** + Atividade 2.
  - `20h20 - 20h40`: **Ciclo 3, Dockerfile e build** + Atividade 3.
  - `20h40 - 20h50`: **Pergunta de Verificação #1** (efemeridade) + Tira-dúvidas do Bloco 1.
  - `20h50 - 21h20`: ☕ **INTERVALO (30 min)**.
  - `21h20 - 21h55`: **Ciclo 4, Multi-stage** + Atividade 4 + **Pergunta de Verificação #2** (multi-stage).
  - `21h55 - 22h13`: **Ciclo 5, Volumes** + Atividade 5 + **Pergunta de Verificação #3** (volume x bind mount).
  - `22h13 - 22h27`: **Ciclo 6, Network e observação** + Atividade 6.
  - `22h27 - 22h35`: **Ciclo 7, Registry e Docker Hub** + Atividade 7.
  - `22h35 - 22h42`: **Agent Skills:** conceito, anatomia do `SKILL.md` e demonstração com o `docker-agent`.
  - `22h42 - 22h50`: Entrega no formulário.
- **Sessão de Perguntas de Verificação** (cada pergunta é feita logo depois do ciclo que a ensina):
  1. *Pergunta 1:* O que acontece com os dados salvos dentro do sistema de arquivos de um container quando ele é destruído sem o uso de volumes?  
     *Resposta Esperada:* Todos os dados salvos na camada gravável do container são perdidos permanentemente, pois o container é efêmero por natureza.
  2. *Pergunta 2:* Qual a principal vantagem do Build Multi-Stage no Dockerfile para ambientes corporativos?  
     *Resposta Esperada:* Permite separar o ambiente de compilação/build do ambiente de execução final, resultando em imagens de produção extremamente leves, sem compiladores ou código-fonte desnecessário, aumentando a segurança e velocidade de deploy.
  3. *Pergunta 3:* Qual a diferença entre um Volume Docker e um Bind Mount, e quando usar cada um?  
     *Resposta Esperada:* Volumes são gerenciados totalmente pelo Docker dentro do host (ideais para bancos e persistência de dados em produção). Bind Mounts mapeiam uma pasta física da máquina host para o container (ideais para ambiente de desenvolvimento local).
- **Entregável Prático:** Fork individual com um commit por etapa (`feat(etapa-N)`), os sete critérios do `verificar.py` atendidos e a imagem do coletor publicada no Docker Hub, com redução mínima de 80% sobre a baseline e o coletor final abaixo de 100 MB.

---

### Aula 04 (25/08/2026) - CHECKPOINT 1 (CP1)
- **Formato:** Avaliação Prática Individual em Laboratório (19h20 às 22h50 com intervalo às 20h50).
- **Escopo Integrado:** PRD/SDD, Git Workflows, Sockets TCP/UDP, Protocolos HTTP/SSE e Conteinerização Multi-Stage com Docker.
- **Entregável:** Repositório no GitHub contendo a solução conteinerizada funcionando e documentada.

---

## Módulo II: POO, SOLID, Design Patterns & Backend Poliglota (Setembro)

### Aula 05 (01/09/2026) - POO, Princípios SOLID & Design Patterns em Java & C#
- **Objetivos de Aprendizagem:** Aplicar conceitos de POO, os 5 princípios SOLID e os padrões Factory Method, Repository e Singleton no desenvolvimento dos microsserviços core em Java e C#.
- **Espiral Pedagógica:** **Recupera Aulas 02 e 03** (Construindo as APIs RESTful corporativas que rodam conteinerizadas no Docker).
- **Desafio do Mini Mundo:** Desenvolver o Bounded Context de Pedidos (Java/Spring Boot) e Faturamento (C#/.NET) com alta manutenibilidade e desacoplamento.
- **Agenda em Minutos:**
  - `19h20 - 19h35`: **Resgate da Espiral:** Evoluindo de scripts simples (Aulas 01-03) para arquiteturas robustas em linguagens fortamente tipadas.
  - `19h35 - 19h55`: Desafio de Negócio: Modelar a regra de Pedidos e Faturamento da *LogiTech* sem criar acoplamento.
  - `19h55 - 20h35`: Teoria: Os 5 princípios SOLID (SRP, OCP, LSP, ISP, DIP). Padrões de Projeto: Factory Method, Repository Pattern e Singleton.
  - `20h35 - 20h50`: **Pergunta de Verificação #1** + Tira-dúvidas.
  - `20h50 - 21h20`: ☕ **INTERVALO (30 min)**.
  - `21h20 - 21h35`: **Perguntas de Verificação #2 e #3**.
  - `21h35 - 22h35`: **Atividade Prática em Dupla:** Criar a API de Pedidos em **Java (Spring Boot 3)** e a API de Faturamento em **C# (.NET 8)** aplicando SOLID, Repository Pattern com JPA/EF Core e Factory para conectores.
  - `22h35 - 22h50`: Validação dos endpoints + Commit no Git.
- **Sessão de Perguntas de Verificação:**
  1. *Pergunta 1:* Como o Princípio da Inversão de Dependência (DIP do SOLID) reduz o acoplamento entre a camada de negócio e o banco de dados?  
     *Resposta Esperada:* Faz com que módulos de alto nível (regras de negócio) dependam de abstrações (interfaces), e não de implementações concretas (ORMs/bancos específicos), permitindo trocar a persistência sem alterar o código de negócio.
  2. *Pergunta 2:* Para que serve o padrão Factory Method e em qual situação do nosso Mini Mundo ele é aplicado?  
     *Resposta Esperada:* Serve para delegar a instanciação de objetos para subclasses ou métodos especializados. É aplicado para criar dinamicamente diferentes conectores de gateway de pagamento/faturamento com base no tipo de cliente.
  3. *Pergunta 3:* Qual o risco de utilizar o padrão Singleton incorretamente em ambientes multithreaded?  
     *Resposta Esperada:* Pode causar condições de corrida (*race conditions*) ou gargalos de concorrência se a instância compartilhada mantiver estado mutável sem o devido controle de sincronização.
- **Entregável Prático:** Os serviços `pedidos` (Java) e `faturamento` (C#) respondendo em `/health`, com as 6 lacunas preenchidas, `mvn test` e `dotnet test` verdes, e `docs/EVIDENCIAS.md` provando a race condition do Singleton antes e depois da correção.

---

### Aula 06 (08/09/2026) - Design Patterns Estruturais & Comportamentais em Node.js & Python
- **Objetivos de Aprendizagem:** Desenvolver microsserviços assíncronos em Node.js (TypeScript) e Python (FastAPI) aplicando os padrões Adapter, Decorator e Strategy.
- **Espiral Pedagógica:** **Recupera Aulas 02, 03 e 05** (Expandindo a arquitetura REST poliglota com microsserviços de apoio).
- **Desafio do Mini Mundo:** Construir o serviço de notificações (Node.js) e o motor de cálculo de frete (Python) permitindo diferentes algoritmos de frete e integrando APIs externas.
- **Agenda em Minutos:**
  - `19h20 - 19h35`: **Resgate da Espiral:** Comparando o modelo síncrono do Java/C# com a concorrência assíncrona do Event Loop em Node/Python.
  - `19h35 - 19h55`: Desafio: Criar algoritmos flexíveis de cálculo de rota e conectores de e-mail sem alterar as regras existentes.
  - `19h55 - 20h35`: Teoria: Padrões Estruturais e Comportamentais — Adapter, Decorator e Strategy. Async/Await e OpenAPI com Pydantic/Zod.
  - `20h35 - 20h50`: **Pergunta de Verificação #1** + Tira-dúvidas.
  - `20h50 - 21h20`: ☕ **INTERVALO (30 min)**.
  - `21h20 - 21h35`: **Perguntas de Verificação #2 e #3**.
  - `21h35 - 22h35`: **Atividade Prática em Dupla:** Desenvolver o motor em **Python (FastAPI)** com o Strategy Pattern (Frete Expresso vs Normal) e o serviço em **Node.js (TypeScript)** usando o Decorator Pattern para logging de notificações.
  - `22h35 - 22h50`: Teste dos contratos OpenAPI no Swagger UI + Commit no Git.
- **Sessão de Perguntas de Verificação:**
  1. *Pergunta 1:* Como o padrão Strategy nos permite adicionar um novo tipo de cálculo de frete sem violar o princípio Open/Closed (OCP)?  
     *Resposta Esperada:* O Strategy encapsula cada algoritmo de frete em uma classe separada que implementa uma interface comum. Para adicionar um novo frete, basta criar uma nova classe sem modificar o código do contexto principal.
  2. *Pergunta 2:* Qual a utilidade do padrão Adapter ao integrar bibliotecas de terceiros ou APIs externas ao nosso sistema?  
     *Resposta Esperada:* Ele atua como um tradutor entre a interface esperada pela nossa aplicação e a interface incompatível da API externa, evitando que mudanças de terceiros quebrem nosso sistema.
  3. *Pergunta 3:* O que é o Decorator Pattern e como ele adiciona funcionalidades a um objeto em tempo de execução?  
     *Resposta Esperada:* É um padrão estrutural que envolve o objeto original em uma nova classe "decoradora", adicionando comportamentos antes ou depois da execução do objeto base sem alterar sua classe.
- **Entregável Prático:** Os serviços `frete` (FastAPI) e `notificacoes` (Node/TS) com as 6 lacunas preenchidas, `pytest` e `vitest` verdes, e uma modalidade nova de frete acrescentada sem modificar a rota, provada por `git diff`.

---

### Aula 07 (15/09/2026) - Docker Compose Multi-Serviço & AI Gateways (Strategy & Facade Patterns)
- **Objetivos de Aprendizagem:** Orquestrar a infraestrutura multi-serviços poliglota com `docker-compose.yml` e implementar uma camada de **AI Gateway** para rotear chamadas de LLM.
- **Espiral Pedagógica:** **Recupera Aulas 03, 05 e 06** (Reunindo todos os 4 serviços poliglotas criados anteriormente em um ambiente orquestrado).
- **Desafio do Mini Mundo:** Subir os serviços de Pedidos (Java), Faturamento (C#), Notificação (Node), Cálculo (Python), PostgreSQL e um AI Gateway usando um único comando.
- **Agenda em Minutos:**
  - `19h20 - 19h35`: **Resgate da Espiral:** Coletando os `Dockerfiles` criados nas Aulas 03, 05 e 06.
  - `19h35 - 19h55`: Desafio: Orquestrar a plataforma *LogiTech* completa e criar um ponto de entrada inteligente para LLMs.
  - `19h55 - 20h35`: Teoria: Sintaxe do Docker Compose, redes virtuais, variáveis de ambiente, volumes e dependências (`depends_on`). Arquitetura de **AI Gateways** (roteamento, fallback, rate limit e caching semântico).
  - `20h35 - 20h50`: **Pergunta de Verificação #1** + Tira-dúvidas.
  - `20h50 - 21h20`: ☕ **INTERVALO (30 min)**.
  - `21h20 - 21h35`: **Perguntas de Verificação #2 e #3**.
  - `21h35 - 22h35`: **Atividade Prática em Grupo:** Escrever o arquivo `docker-compose.yml` unificando a aplicação e configurando o LiteLLM / AI Gateway com fallback entre OpenAI e modelos locais.
  - `22h35 - 22h50`: Execução do `docker-compose up` em sala + Commit no Git.
- **Sessão de Perguntas de Verificação:**
  1. *Pergunta 1:* Qual o papel da propriedade `depends_on` no Docker Compose e por que ela isoladamente não garante que o banco de dados esteja pronto para receber conexões?  
     *Resposta Esperada:* A propriedade define a ordem de inicialização dos containers, mas apenas aguarda o container do banco subir, e não a conclusão da inicialização interna do processo do banco de dados (sendo necessário scripts de healthcheck).
  2. *Pergunta 2:* Como o padrão Facade é utilizado na arquitetura de um AI Gateway corporativo?  
     *Resposta Esperada:* Ele fornece uma interface única e simplificada para a aplicação consumidora, ocultando a complexidade de integração, autenticação e formato de payload de múltiplos provedores de IA diferentes.
  3. *Pergunta 3:* O que é o Caching Semântico em um AI Gateway e como ele reduz custos operacionais?  
     *Resposta Esperada:* É um cache que armazena respostas de LLMs com base na similaridade de significado (vetores) das perguntas, evitando fazer novas chamadas pagas à API do provedor para perguntas conceitualmente idênticas.
- **Entregável Prático:** `docker-compose.yml` com os 8 serviços da plataforma, `docker compose ps` mostrando todos saudáveis, o fallback do AI Gateway acionado de verdade no log, e o painel de telemetria lendo do coletor por HTTP, sem o arquivo compartilhado.

---

### Aula 08 (22/09/2026) - Orquestração de Agentes (Command Pattern) & Git Worktrees I
- **Objetivos de Aprendizagem:** Capacitar o assistente de IA a executar ações reais no backend via Function Calling (Command Pattern) e introduzir a técnica avançada de **Git Worktrees** para desenvolvimento paralelo com agentes.
- **Espiral Pedagógica:** **Recupera Aulas 06 e 07** (Conectando o agente em Python ao AI Gateway e às APIs poliglotas).
- **Desafio do Mini Mundo:** Permitir que o atendente virtual consulte status e altere endereços de entregas no sistema, utilizando **Git Worktrees** para testar múltiplos agentes sem conflitos de branch.
- **Agenda em Minutos:**
  - `19h20 - 19h35`: **Resgate da Espiral:** Conectando a especificação OpenAPI da Aula 06 com a camada de IA da Aula 07.
  - `19h35 - 19h55`: Desafio: Permitir que o agente de IA execute comandos no sistema de forma segura e paralela.
  - `19h55 - 20h35`: Teoria: Function Calling / Tool Calling, JSON Schema Enforcement, Command Pattern em IA. Conceito e comandos práticos de **Git Worktrees** (`git worktree add`, `git worktree list`).
  - `20h35 - 20h50`: **Pergunta de Verificação #1** + Tira-dúvidas.
  - `20h50 - 21h20`: ☕ **INTERVALO (30 min)**.
  - `21h20 - 21h35`: **Perguntas de Verificação #2 e #3**.
  - `21h35 - 22h35`: **Atividade Prática em Dupla:** Criar worktrees isoladas no Git (`worktree-agent-orders` e `worktree-agent-support`) e programar o agente em Python para invocar as funções da API de Pedidos.
  - `22h35 - 22h50`: Validação das chamadas de função do agente + Tira-dúvidas.
- **Sessão de Perguntas de Verificação:**
  1. *Pergunta 1:* Por que o uso tradicional de `git checkout` falha quando temos múltiplos Agentes de IA trabalhando simultaneamente no mesmo repositório local?  
     *Resposta Esperada:* Porque o `git checkout` altera o diretório de trabalho único. Se um agente modificar arquivos enquanto outro agente está executando ou compilando, ocorrerão erros de conflito, arquivos bloqueados e perda de contexto.
  2. *Pergunta 2:* Como o Command Pattern garante segurança e auditabilidade quando uma IA executa Function Calling no sistema?  
     *Resposta Esperada:* Ele converte a intenção da IA em um objeto de comando bem definido e validado por um JSON Schema estrito, permitindo interceptar, autorizar, registrar e até desfazer a ação antes de executá-la no banco.
  3. *Pergunta 3:* Qual o comando Git para criar um novo diretório de trabalho ligado à branch `feature/agent-tools` sem sair da pasta atual?  
     *Resposta Esperada:* `git worktree add ../pasta-worktree feature/agent-tools`.
- **Entregável Prático:** Agente com as 5 lacunas preenchidas, `docs/AUDITORIA.md` com no mínimo 3 execuções autorizadas e 1 recusa registrada, `pytest` verde, e `git worktree list` mostrando as duas worktrees com os dois agentes rodando em paralelo.

---

### Aula 09 (29/09/2026) - CHECKPOINT 2 (CP2)
- **Formato:** Avaliação Prática em Laboratório (19h20 às 22h50 com intervalo às 20h50).
- **Escopo Integrado:** POO, SOLID, Design Patterns (Factory, Strategy, Command), Backend Poliglota (Java/C#/Node/Python), Docker Compose, AI Gateway e Function Calling.
- **Entregável:** Aplicação multi-serviço rodando no Docker Compose com suporte a Agente de IA.

---

## Módulo III: Testes de Unidade, Frontend Enterprise, SQL, RAG & MCP (Outubro)

### Aula 10 (06/10/2026) - Testes de Unidade (TDD / Mocks) & Frontend Enterprise I: React (TypeScript)
- **Objetivos de Aprendizagem:** Aplicar a camada de testes de unidade com TDD/Mocks nas regras de negócio e desenvolver uma interface SPA reativa em React (TypeScript).
- **Espiral Pedagógica:** **Recupera Aulas 05 e 06** (Criando testes automatizados para as APIs e desenvolvendo a interface de usuário).
- **Desafio do Mini Mundo:** Garantir 100% de cobertura nos cálculos de frete via **Testes de Unidade** e criar o Portal do Cliente em React para rastreamento de pedidos.
- **Agenda em Minutos:**
  - `19h20 - 19h35`: **Resgate da Espiral:** A importância dos testes automatizados de unidade antes de expor a aplicação para telas de frontend.
  - `19h35 - 19h55`: Desafio: Garantir a qualidade das regras de frete e criar o portal web em React.
  - `19h55 - 20h35`: Teoria: Pirâmide de Testes (foco na base de Unidade), TDD, Mocks/Stubs com PyTest/Vitest/JUnit. Frontend React: Componentes, JSX, Virtual DOM, Hooks (`useState`, `useEffect`) e Axios.
  - `20h35 - 20h50`: **Pergunta de Verificação #1** + Tira-dúvidas.
  - `20h50 - 21h20`: ☕ **INTERVALO (30 min)**.
  - `21h20 - 21h35`: **Perguntas de Verificação #2 e #3**.
  - `21h35 - 22h35`: **Atividade Prática em Dupla:** Escrever suíte de testes de unidade com Mocks para o serviço de frete + criar a SPA em **React (TypeScript)** consumindo os dados da API.
  - `22h35 - 22h50`: Execução da suíte de testes e visualização da tela no navegador + Commit no Git.
- **Sessão de Perguntas de Verificação:**
  1. *Pergunta 1:* O que é a Pirâmide de Testes e por que os testes de unidade devem constituir a maior parte da nossa suíte de testes?  
     *Resposta Esperada:* A pirâmide de testes orienta a proporção de cada tipo de teste. Testes de unidade ficam na base por serem extremamente rápidos de executar, baratos de manter e fornecerem feedback imediato sobre pequenas partes do código.
  2. *Pergunta 2:* Qual a diferença entre um Mock e um Stub em testes de unidade?  
     *Resposta Esperada:* Um Stub fornece respostas pré-programadas para chamadas feitas durante o teste. Um Mock vai além: ele verifica se determinadas chamadas, parâmetros e ordens de execução realmente ocorreram durante o teste.
  3. *Pergunta 3:* Como o Virtual DOM do React otimiza a atualização da interface do usuário em comparação com a manipulação direta do DOM do navegador?  
     *Resposta Esperada:* O React cria uma cópia em memória do DOM. Quando o estado muda, ele compara o novo Virtual DOM com o anterior (algoritmo de diffing) e atualiza no navegador real apenas os elementos que realmente mudaram.
- **Entregável Prático:** Suíte de testes de unidade executando com 100% de aprovação + Portal do Cliente em React funcional.

---

### Aula 11 (13/10/2026) - Frontend Enterprise II: Angular (Observer Pattern & RxJS)
- **Objetivos de Aprendizagem:** Desenvolver o painel administrativo em Angular aplicando Injeção de Dependência, Módulos/Services e o padrão **Observer** com **RxJS**.
- **Espiral Pedagógica:** **Recupera Aulas 05, 06 e 10** (Comparando a abordagem da biblioteca React com a arquitetura opinada do framework Angular).
- **Desafio do Mini Mundo:** Construir o dashboard operacional em Angular para a equipe interna da *LogiTech* acompanhar a frota em tempo real e consultar o faturamento, em dois fluxos assíncronos concorrentes.

> Escopo ajustado pela `ADR-008`: o painel consome a telemetria que o serviço `painel` já expõe desde a Aula 02 e o `faturamento` em .NET da Aula 05, em vez de um cadastro de motoristas que não existe no contrato da plataforma. A escolha é o que dá dois fluxos contínuos e concorrentes ao painel, que é o caso que justifica RxJS e dá lastro à Pergunta de Verificação 3.
- **Agenda em Minutos:**
  - `19h20 - 19h35`: **Resgate da Espiral:** Comparando a flexibilidade do React (Aula 10) com a estrutura opinada do Angular.
  - `19h35 - 19h55`: Desafio: Criar um painel corporativo complexo com múltiplos fluxos reativos de dados.
  - `19h55 - 20h35`: Teoria: Arquitetura do Angular, Módulos, Standalone Components, Injeção de Dependência nativa e o **Observer Pattern** com **RxJS** (`Observables`, `Subjects`, `BehaviorSubjects`, operadores `map`, `switchMap`).
  - `20h35 - 20h50`: **Pergunta de Verificação #1** + Tira-dúvidas.
  - `20h50 - 21h20`: ☕ **INTERVALO (30 min)**.
  - `21h20 - 21h35`: **Perguntas de Verificação #2 e #3**.
  - `21h35 - 22h35`: **Atividade Prática em Dupla:** Criar o dashboard administrativo em **Angular** consumindo a API C#/.NET e utilizando RxJS para manipular e filtrar fluxos reativos de dados.
  - `22h35 - 22h50`: Demonstração da aplicação Angular em execução + Commit no Git.
- **Sessão de Perguntas de Verificação:**
  1. *Pergunta 1:* Como o padrão Observer implementado pelo RxJS no Angular difere do modelo tradicional de requisição/resposta via Promises?  
     *Resposta Esperada:* Promises lidam com um único evento futuro assíncrono. Observables do RxJS são fluxos (*streams*) que podem emitir zero, um ou múltiplos valores ao longo do tempo, permitindo aplicar operadores de transformação em tempo real.
  2. *Pergunta 2:* O que é Injeção de Dependência no Angular e quais seus benefícios para a testabilidade da aplicação?  
     *Resposta Esperada:* É um padrão onde o Angular fornece automaticamente as instâncias dos serviços de que um componente precisa, em vez de o componente criá-las manualmente. Isso permite trocar serviços reais por Mocks facilmente nos testes.
  3. *Pergunta 3:* Para que serve o operador `switchMap` no RxJS durante uma busca em tempo real na interface?  
     *Resposta Esperada:* Ele cancela a inscrição da requisição anterior caso uma nova busca seja disparada antes que a anterior termine, evitando respostas desordenadas (*race conditions*) e economizando recursos de rede.
- **Entregável Prático:** Dashboard administrativo em Angular utilizando RxJS e serviços injetados.

---

### Aula 12 (20/10/2026) - PostgreSQL: do relacional ao vetorial (SQL, `pgvector`, RAG & MCP)
- **Objetivos de Aprendizagem:** Consultar e modelar diretamente em SQL o banco relacional que os serviços da plataforma vinham usando por meio de ORM, configurar busca vetorial com `pgvector`, construir um pipeline RAG e desenvolver um servidor **Model Context Protocol (MCP)** em TypeScript.
- **Espiral Pedagógica:** **Recupera Aulas 05, 06, 07, 08 e 10** (Abrindo o banco por baixo do Repository Pattern e expandindo a inteligência da aplicação com busca semântica em contratos).
- **Desafio do Mini Mundo:** Consultar diretamente a base da plataforma, permitir que motoristas e clientes tirem dúvidas sobre contratos complexos de transporte via busca semântica RAG, e expor serviços da empresa para agentes parceiros via MCP.
- **Agenda em Minutos:**
  - `19h20 - 19h35`: **Resgate da Espiral:** O banco que sempre esteve lá. Abrir no `psql` as tabelas que o Hibernate e o EF Core criaram nas Aulas 05 e 06, e constatar que ninguém da turma escreveu aquela SQL.
  - `19h35 - 19h50`: Desafio: Consultar dados que o ORM não modela e resolver buscas em documentos não estruturados.
  - `19h50 - 20h35`: Teoria: SQL relacional (DDL, chave estrangeira e restrições, `SELECT`, `JOIN`, `ORDER BY`, `LIMIT`, índices e leitura de plano de execução com `EXPLAIN`). Sobre essa base, embeddings, distância de cosseno e busca por similaridade com `pgvector`, apresentada como mais um `ORDER BY`. Pipeline RAG (Chunking, Ingestion, Retrieval).
  - `20h35 - 20h50`: **Pergunta de Verificação #1** + Tira-dúvidas.
  - `20h50 - 21h20`: ☕ **INTERVALO (30 min)**.
  - `21h20 - 21h32`: **Perguntas de Verificação #2 e #3**.
  - `21h32 - 21h42`: Teoria, bloco curto: especificação do **Model Context Protocol (MCP)** (Servers, Resources, Tools, Prompts) e o transporte `stdio`.
  - `21h42 - 22h35`: **Atividade Prática em Dupla:** Inspecionar os schemas existentes no `psql`, escrever a DDL do schema `conhecimento` à mão, consultar com `JOIN`, ativar a extensão `pgvector`, implementar o pipeline RAG em Python, criar o índice e comparar o `EXPLAIN`, e expor a API de Pedidos por um servidor MCP em TypeScript.
  - `22h35 - 22h50`: Teste de consultas semânticas com citação da fonte e do servidor MCP + Commit no Git.
- **Sessão de Perguntas de Verificação:**
  1. *Pergunta 1:* Qual a diferença entre uma busca tradicional por palavra-chave (keyword search) e uma busca por similaridade de vetores (embeddings)?  
     *Resposta Esperada:* A busca por palavras-chaves exige a correspondência exata dos termos buscados. A busca por vetores compara o significado semântico do texto no espaço vetorial, encontrando resultados relevantes mesmo se usarem palavras diferentes (sinônimos/conceitos).
  2. *Pergunta 2:* O que é o Model Context Protocol (MCP) e qual problema de integração ele resolve entre aplicações e LLMs?  
     *Resposta Esperada:* O MCP é um protocolo aberto que padroniza como as aplicações fornecem contexto (dados, ferramentas e prompts) para os modelos de IA, substituindo integrações customizadas e proprietárias por uma interface universal reutilizável.
  3. *Pergunta 3:* A busca por similaridade já devolve o resultado certo antes de existir qualquer índice. Então por que criar um índice vetorial, e o que muda no `EXPLAIN`?  
     *Resposta Esperada:* Sem índice o PostgreSQL faz varredura sequencial e calcula a distância linha a linha, o que é exato mas cresce com o tamanho da tabela. Com um índice vetorial como o `hnsw` o plano passa a usar busca por índice e o tempo deixa de crescer na mesma proporção. A contrapartida é que esse índice é **aproximado**: ele troca uma parcela de precisão na recuperação por velocidade, ao contrário do índice B-tree de uma coluna comum.
- **Entregável Prático:** Schema relacional criado e consultado por SQL escrita pelo aluno, pipeline RAG funcional no PostgreSQL (`pgvector`) devolvendo o trecho certo com citação do contrato de origem, e servidor MCP em TypeScript commitado no Git.

> **Mudança registrada na `ADR-008`, em 31/07/2026.** A aula ganhou SQL relacional porque o levantamento mostrou que não havia um único arquivo `.sql` no acervo: o aluno persistia em PostgreSQL o semestre inteiro sem escrever SQL. A Pergunta de Verificação 3 deixou de cobrar a lista de conceitos do MCP, que passou a ser conteúdo do bloco curto de teoria, e passou a cobrar índice e plano de execução. O bloco prático encolheu de 60 para 53 minutos; a ordem de corte está declarada no README do laboratório e começa pelo `EXPLAIN` comparativo, que vira demonstração do professor.

---

### Aula 13 (27/10/2026) - CHECKPOINT 3 (CP3)
- **Formato:** Avaliação Prática Individual em Laboratório (19h20 às 22h50 com intervalo às 20h50).
- **Escopo Integrado:** Testes de Unidade (TDD/Mocks), Frontend Enterprise (React/Angular), SQL relacional (DDL, `JOIN`, índices), Persistência Vetorial (`pgvector`), Arquitetura RAG e Servidores MCP.
- **Entregável:** Aplicação Frontend integrada ao Backend com suporte a testes de unidade e funcionalidade de RAG ou MCP, apoiada em schema criado e consultado por SQL escrita pelo aluno.

---

## Módulo IV: Segurança Enterprise, Hardening & Global Solution (Novembro e Dezembro)

### Aula 14 (03/11/2026) - Segurança Web Enterprise (OAuth 2.0, OIDC, JWT, RBAC) & Git Worktrees II
- **Objetivos de Aprendizagem:** Implementar autenticação corporativa via OAuth 2.0/OIDC com Keycloak, validar tokens JWT nas APIs, aplicar RBAC e utilizar **Git Worktrees** para isolar o desenvolvimento de segurança.
- **Espiral Pedagógica:** **Recupera Aulas 05, 06, 08, 10 e 11** (Protegendo todas as rotas de backend e telas de frontend criadas ao longo do semestre).
- **Desafio do Mini Mundo:** Garantir que apenas motoristas e clientes autenticados consigam acessar os serviços da *LogiTech* de acordo com suas permissões (RBAC).
- **Agenda em Minutos:**
  - `19h20 - 19h35`: **Resgate da Espiral:** Retomando as rotas expostas das Aulas 05-06 e adicionando a camada de proteção.
  - `19h35 - 19h55`: Desafio: Autenticar usuários via provedor de identidade e propagar credenciais com segurança.
  - `19h55 - 20h35`: Teoria: OAuth 2.0 (PKCE Flow), OpenID Connect (OIDC), estrutura de tokens JWT (Header, Payload, Signature, JWKS), controle de acesso RBAC. Uso avançado de **Git Worktrees** para refatoração de segurança com IAs.
  - `20h35 - 20h50`: **Pergunta de Verificação #1** + Tira-dúvidas.
  - `20h50 - 21h20`: ☕ **INTERVALO (30 min)**.
  - `21h20 - 21h35`: **Perguntas de Verificação #2 e #3**.
  - `21h35 - 22h35`: **Atividade Prática em Grupo:** Criar a worktree `/worktrees/security`, subir o Keycloak no Compose, proteger a API Java/Node com middleware de validação JWT e aplicar restrições de Roles (RBAC).
  - `22h35 - 22h50`: Teste de envio de requisições autenticadas via Postman/cURL + Merge do PR no Git.
- **Sessão de Perguntas de Verificação:**
  1. *Pergunta 1:* Qual a função da assinatura em um token JWT e por que o servidor backend pode confiar nos dados do payload sem consultar o banco a cada requisição?  
     *Resposta Esperada:* A assinatura garante a integridade e autenticidade do token. Se a chave pública (JWKS) do servidor validar que a assinatura foi gerada pela chave privada do Provedor de Identidade, o backend sabe que os dados do payload não foram adulterados.
  2. *Pergunta 2:* O que é o fluxo OAuth 2.0 Authorization Code com PKCE e por que ele é recomendado para aplicações SPA (React/Angular)?  
     *Resposta Esperada:* É um fluxo seguro onde a aplicação SPA não lida nem armazena segredos de cliente (*client secret*). O PKCE gera um par de códigos dinâmicos (*code verifier* e *code challenge*) impedindo ataques de interceptação do código de autorização em clientes públicos.
  3. *Pergunta 3:* Como o modelo RBAC (Role-Based Access Control) organiza a autorização de usuários no sistema?  
     *Resposta Esperada:* Ele associa permissões a papéis (*roles*, ex: `ADMIN`, `DRIVER`, `CUSTOMER`) e atribui esses papéis aos usuários. O código verifica se o usuário possui a *role* necessária para acessar determinado recurso.
- **Entregável Prático:** As 6 lacunas preenchidas; `curl` sem token devolvendo 401 e com papel errado devolvendo 403, os dois registrados; `PAPEIS_NO_TOKEN` copiado de `realm_access.roles`; `git worktree list` com as duas worktrees; e as suítes verdes nas quatro stacks.

---

### Aula 15 (10/11/2026) - Segurança AI-First (OWASP Top 10 for LLMs) & Trivy Container Scan
- **Objetivos de Aprendizagem:** Aplicar sanitização e guardrails de segurança contra ataques de Prompt Injection no AI Gateway e realizar varreduras de vulnerabilidade de SO em containers com Trivy.
- **Espiral Pedagógica:** **Recupera Aulas 03, 07, 12 e 14** (Hardening completo da infraestrutura de containers Docker e das chamadas de IA).
- **Desafio do Mini Mundo:** Proteger a *LogiTech* contra injeções de código/prompts maliciosos no assistente virtual e eliminar vulnerabilidades de software nas imagens Docker.
- **Agenda em Minutos:**
  - `19h20 - 19h35`: **Resgate da Espiral:** Analisando os containers (Aula 03) e o AI Gateway (Aula 07) sob a perspectiva de segurança.
  - `19h35 - 19h55`: Desafio: Proteger os modelos de IA da empresa contra Prompt Injection e garantir containers limpos.
  - `19h55 - 20h35`: Teoria: As vulnerabilidades do **OWASP Top 10 for LLMs** (Prompt Injection Direto/Indireto, Sensitive Information Disclosure). Ferramentas de análise estática de containers (**Trivy** / `docker scan`).
  - `20h35 - 20h50`: **Pergunta de Verificação #1** + Tira-dúvidas.
  - `20h50 - 21h20`: ☕ **INTERVALO (30 min)**.
  - `21h20 - 21h35`: **Perguntas de Verificação #2 e #3**.
  - `21h35 - 22h35`: **Atividade Prática em Grupo:** Executar o `trivy image` nas imagens do projeto e corrigir pacotes vulneráveis no Dockerfile Multi-Stage + implementar filtro de sanitização contra Prompt Injection no AI Gateway.
  - `22h35 - 22h50`: Relatório de scan do Trivy sem vulnerabilidades críticas + Commit no Git.
- **Sessão de Perguntas de Verificação:**
  1. *Pergunta 1:* O que é um ataque de Prompt Injection Direto e como ele se assemelha ao ataque clássico de SQL Injection?  
     *Resposta Esperada:* Ocorre quando o usuário envia instruções maliciosas no texto de entrada que sobrescrevem as instruções de sistema (*system prompt*) do LLM, fazendo a IA ignorar suas regras de segurança originais. Assim como no SQL Injection, a entrada do usuário altera a lógica de execução.
  2. *Pergunta 2:* Como a ferramenta Trivy auxilia no processo de DevSecOps durante o build de containers Docker?  
     *Resposta Esperada:* O Trivy analisa a imagem Docker procurando por vulnerabilidades conhecidas (CVEs) tanto no sistema operacional de base quanto nas bibliotecas de dependências (npm, pip, maven), permitindo barrar imagens inseguras na esteira de CI.
  3. *Pergunta 3:* Qual a estratégia recomendada para evitar que um modelo de IA exiba informações sensíveis (PII / Sensitive Information Disclosure)?  
     *Resposta Esperada:* Aplicar filtros de sanitização de entrada e saída (Guardrails), mascarar dados sensíveis (ex: CPF, cartão) antes de enviar o prompt ao provedor de LLM e utilizar modelos locais para dados estritamente confidenciais.
- **Entregável Prático:** As 6 lacunas preenchidas; `INJECAO_ANTES` e `INJECAO_DEPOIS` registrados; `CVES_CRITICAL_DEPOIS` igual a zero com a data da varredura; `docs/EXCECOES.md` com cada HIGH aceita, justificada e datada; e a formulação que furou o próprio filtro registrada.

---

### Aula 16 (17/11/2026) - Integração Enterprise End-to-End & Simulado da Global Solution
- **Objetivos de Aprendizagem:** Realizar o deploy integrado e testes ponta a ponta de todo o ecossistema da *LogiTech Enterprise* (React + Angular + Java + C# + Python + Node + Docker Compose + Keycloak + RAG/MCP + Security).
- **Espiral Pedagógica:** **Consolidação Total da Espiral do Semestre (Aulas 01 a 15)**.
- **Desafio do Mini Mundo:** Colocar a plataforma *LogiTech Enterprise* inteira em execução com um único `docker-compose up` e validar todos os fluxos de integração.
- **Agenda em Minutos:**
  - `19h20 - 19h35`: **Resgate Geral:** Abertura do Hackathon em Sala e revisão do checklist da Global Solution.
  - `19h35 - 20h50`: **Hackathon Parte I (Bloco 1):** Grupos trabalham na resolução dos últimos pontos de integração dos serviços de frontend, backend e IA.
  - `20h50 - 21h20`: ☕ **INTERVALO (30 min)**.
  - `21h20 - 22h35`: **Hackathon Parte II (Bloco 2):** Execução do simulado da banca da Global Solution, testes de comunicação entre containers e validação das rotas protegidas.
  - `22h35 - 22h50`: Orientações finais para a apresentação oficial da banca na semana seguinte + Push final no GitHub.
- **Sessão de Perguntas de Verificação (Checklist da GS):**
  1. *Pergunta 1:* Todos os microsserviços sobem automaticamente via `docker-compose up` sem a necessidade de intervenção manual? (Sim/Não - Verificação de scripts e variáveis).
  2. *Pergunta 2:* A autenticação via Keycloak está protegendo adequadamente tanto as rotas de backend quanto os guardas de rotas no frontend React/Angular? (Validação via Token JWT).
  3. *Pergunta 3:* O AI Gateway e o servidor MCP estão integrados e respondendo corretamente às chamadas de Function Calling e busca semântica RAG? (Validação funcional).
- **Entregável Prático:** As 5 frentes verdes no `verificar.py`; `TEMPO_ATE_TODOS_SAUDAVEIS_S` e `MEMORIA_TOTAL_MIB` medidos na máquina do grupo; o roteiro de apresentação de 10 minutos escrito, com quem fala o quê; e o repositório subindo a plataforma do zero.

---

### Semanas 17 & 18 (24/11/2026 e 01/12/2026) - GLOBAL SOLUTION (GS)
- **Atividade Institucional FIAP:** Apresentações oficiais dos projetos integrados para a Banca de Professores.

---

### Aula 17 (08/12/2026) - Feedback GS, Vista de Provas & Roadmap 2027-1
- **Fechamento do Semestre:** Retrospectiva do semestre, feedback individualizado por grupo, lançamento de notas e apresentação da espiral avançada do 2º semestre (Arquitetura de Microsserviços Distribuídos, Kubernetes, Redis, Kafka e Terraform em 2027-1).

---

### Encontro Final (15/12/2026) - Período de Exames Acadêmicos
- **Atendimento Individual:** Realização de provas substitutivas e atendimento de alunos em exame.
