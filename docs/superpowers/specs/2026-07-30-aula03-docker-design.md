# Aula 03, Docker I: desenho validado

- **Data:** 2026-07-30
- **Aula:** 03, de 18/08/2026, Módulo I
- **Título:** Docker I: Engine, Imagens, Dockerfile Multi-Stage e Persistência
- **Status:** aprovado em brainstorming, pendente de revisão do professor
- **Entregáveis:** deck `aulas-1sem/aulas/aula03.html` e lab kit `josercf/mwe-2026-2-lab03-docker`

---

## 1. Problema

O deck atual da Aula 03 tem 136 linhas de saída crua de scaffolder, sem figura e
com quizzes genéricos. O laboratório tem dois arquivos soltos, `Dockerfile` e
`app.py`, sem README e sem ligação com o case.

A turma chega com **conhecimento zero de containers**, e a aula precisa cobrir o
tema em 360 graus, do isolamento de processos no Linux até a publicação de uma
imagem em registry público. A Aula 04, uma semana depois, é o CP1, uma prova
prática individual que cobra conteinerização.

O professor pediu três mudanças em relação ao padrão do acervo:

1. **Prática a cada etapa**, e não um laboratório único no fim.
2. **Atividade individual**, para que todos executem, e não em dupla.
3. **Muito recurso visual e animação**, porque o assunto é espacial e sequencial.

---

## 2. Decisões

| # | Decisão | Alternativa descartada e por quê |
|---|---|---|
| D1 | A aula vira **7 ciclos de teoria curta seguida de prática individual**, com os 3 quizzes e o intervalo nos horários oficiais | Manter o bloco teórico de 40 min com micro-práticas dentro dele: preserva a agenda oficial mas concentra a prática, que é justamente o que o professor pediu para dissolver |
| D2 | O aluno conteineriza uma **cópia congelada** dos serviços da Aula 02, entregue pronta em `servicos/` | Usar o fork da Aula 02 de cada aluno: quem não terminou a Aula 02 travaria no ciclo 3 e não se recuperaria, o que é fatal em atividade progressiva |
| D3 | Conta no **Docker Hub é pré-requisito anunciado antes da aula** | Criar a conta em sala: a verificação por e-mail custa de 5 a 10 min e trava parte da turma no ciclo mais tardio da noite |
| D4 | **Docker Compose fica fora**, com teaser no encerramento | Incluir: o `PLANO_DE_ENSINO.md` aloca Compose na Aula 07, e antecipar esvazia aquela aula |
| D5 | **Agent Skills entram como demonstração do professor** mais etapa 8 bônus feita em casa | Ciclo 8 completo com prática: exigiria rebaixar o ciclo de rede a demonstração, e 30 alunos disparando agente ao mesmo tempo estouraria a cota do free tier do GitHub Models |
| D6 | O modelo local do lab03 passa a ser **`qwen3.5:2b`** | `gemma4:e2b`, que tem function calling nativo mas ocupa 7,2 GB no Ollama contra 8 GB de RAM da máquina padrão do Codespaces, disputados com o Docker-in-Docker |

D1, D5 e D6 divergem de documentos já aprovados e são registradas na
`docs/adrs/ADR-004-formato-progressivo-da-aula-03.md`.

---

## 3. Agenda

Total de 210 min, das 19h20 às 22h50, com intervalo obrigatório de 30 min às 20h50.

### Bloco 1, das 19h20 às 20h50

| Início | Conteúdo | Teoria | Prática |
|---|---|---|---|
| 19h20 | Resgate da espiral | 10 | |
| 19h30 | Desafio do Mini Mundo | 10 | |
| 19h40 | C1 Isolamento de processos no Linux | 12 | 8 |
| 20h00 | C2 Imagem, camadas e efemeridade | 12 | 8 |
| 20h20 | C3 Dockerfile e build | 12 | 8 |
| 20h40 | Quiz 1 | 10 | |

### Intervalo, das 20h50 às 21h20

### Bloco 2, das 21h20 às 22h50

| Início | Conteúdo | Teoria | Prática |
|---|---|---|---|
| 21h20 | Quizzes 2 e 3 | 15 | |
| 21h35 | C4 Multi-stage | 10 | 10 |
| 21h55 | C5 Volumes | 10 | 8 |
| 22h13 | C6 Network e observação | 8 | 6 |
| 22h27 | C7 Registry e Docker Hub | 8 | |
| 22h35 | Agent Skills: conceito e demonstração | 7 | |
| 22h42 | Entrega no formulário | 8 | |

**Ordem de corte se atrasar:** primeiro C6 vira demonstração do professor, depois
a segunda metade de C5. C7 e as Agent Skills nunca saem, porque C7 fecha o pedido
do Docker Hub e as skills são o conteúdo novo pedido pelo professor.

---

## 4. Escopo dos 360 graus

**Dentro:** processo Linux e `chroot`; os seis namespaces (pid, net, mnt, uts,
ipc, user); cgroups; container como processo isolado; container x máquina
virtual; arquitetura CLI, daemon, containerd e runc; imagem x container; union
filesystem e camadas; camada gravável e efemeridade; ciclo de vida do container;
`run`, `ps`, `logs`, `exec`, `stop`, `rm`; Dockerfile instrução a instrução;
`CMD` x `ENTRYPOINT`; cache de camadas; `.dockerignore` e contexto de build;
build multi-stage; escolha de imagem base entre full, slim, alpine e distroless;
usuário não-root; volume nomeado, bind mount e tmpfs; redes bridge, host e none;
DNS por nome de container; publicação de porta; `docker stats`, `docker inspect`
e limites `--memory` e `--cpus`; registry, repositório, tag e digest; `login`,
`tag`, `push` e `pull`; Agent Skills e o formato `SKILL.md`.

**Fora, com dono definido:** Docker Compose fica na Aula 07; Trivy e hardening de
imagem ficam na Aula 15; Swarm e Kubernetes ficam no segundo semestre; BuildKit
avançado e `buildx` ficam fora do programa.

---

## 5. Mapa do deck

55 slides. Numeração final confirmada pela renumeração de rodapé ao término.

```
 1  cover-slide     Capa
 2  title-slide     Aula 03, Docker I
 3  content-slide   Agenda do encontro, com os 7 ciclos e o intervalo
 4  content-slide   Como a aula de hoje funciona: ciclo teoria-prática, individual
 5  content-slide   Pré-requisitos: conta no Docker Hub e fork do lab
 6  content-slide   Resgate da espiral: o que as Aulas 01 e 02 entregaram
 7  content-slide   Desafio do Mini Mundo: "na minha máquina funciona"

    CICLO 1, Isolamento de processos
 8  content-slide   Um processo Linux comum: tudo compartilhado          [ANIM 1]
 9  content-slide   chroot: o primeiro isolamento e por que não basta
10  content-slide   Namespaces: os seis tipos                            [ANIM 2]
11  content-slide   cgroups: o limite de CPU e de memória                [ANIM 3]
12  content-slide   Container = processo + namespaces + cgroups + rootfs
13  content-slide   Container x máquina virtual                          [figure-split]
14  content-slide   A arquitetura: CLI, daemon, containerd, runc         [ANIM 4]
15  exercise-slide  ATIVIDADE 1: ver os namespaces na prática

    CICLO 2, Imagem, camadas e efemeridade
16  content-slide   Imagem x container: molde e instância
17  content-slide   Camadas e union filesystem                           [ANIM 5]
18  content-slide   A camada gravável morre junto com o container
19  content-slide   Ciclo de vida do container                           [SVG estados]
20  content-slide   Os comandos que você vai usar sempre
21  exercise-slide  ATIVIDADE 2: rodar o coletor sem escrever Dockerfile

    CICLO 3, Dockerfile e build
22  content-slide   O Dockerfile: cada instrução vira uma camada         [SVG]
23  content-slide   As instruções que importam
24  content-slide   CMD x ENTRYPOINT                                     [side-by-side]
25  content-slide   Cache de camadas: a ordem das linhas decide          [ANIM 6]
26  content-slide   .dockerignore e o contexto de build
27  exercise-slide  ATIVIDADE 3: escrever o Dockerfile.coletor

28  quiz-slide      Quiz 1: vantagem do multi-stage
29  content-slide   Intervalo, 30 min
30  quiz-slide      Quiz 2: volume x bind mount
31  quiz-slide      Quiz 3: efemeridade da camada gravável

    CICLO 4, Multi-stage
32  content-slide   O problema: 1 GB para rodar um script                [SVG comparativo]
33  content-slide   Multi-stage: estágio builder e estágio runtime       [ANIM 7]
34  content-slide   A base importa: full, slim, alpine, distroless       [tabela]
35  content-slide   Usuário não-root e o que mais entra na imagem
36  exercise-slide  ATIVIDADE 4: multi-stage dos dois serviços

    CICLO 5, Volumes
37  content-slide   Onde os dados da LogiTech estão morrendo
38  content-slide   Volume nomeado, bind mount e tmpfs                   [SVG 3 colunas]
39  content-slide   Os comandos de volume
40  exercise-slide  ATIVIDADE 5: o log sobrevive ao docker rm

    CICLO 6, Network e observação
41  content-slide   As redes do Docker: bridge, host, none               [SVG]
42  content-slide   DNS por nome de container                            [ANIM 8]
43  content-slide   Publicação de porta e observação com stats e inspect
44  exercise-slide  ATIVIDADE 6: logitech-net e docker stats

    CICLO 7, Registry
45  content-slide   Registry, repositório, tag e digest                  [SVG]
46  content-slide   Docker Hub: login, tag, push                         [ANIM 9]
47  exercise-slide  ATIVIDADE 7: publique a sua imagem

    Agent Skills
48  content-slide   IA que constrói container: o que é uma Agent Skill
49  content-slide   Anatomia do SKILL.md
50  content-slide   Um arquivo, três agentes                             [SVG]

    Encerramento
51  content-slide   O que vai no seu repositório: checklist da entrega
52  content-slide   Formulário de entrega, com iframe
53  content-slide   O que vem: CP1 em 25/08 e Compose na Aula 07
54  content-slide   Referências, com id="ref-slide"
55  end-slide       Copyright do professor
```

### As nove animações

Todas em SVG inline, ciclo de 5 a 8 s, `repeatCount="indefinite"`, cada uma com
`<figcaption>` descrevendo a sequência completa, porque no PDF a animação congela
em um quadro qualquer.

| # | Slide | O que anima |
|---|---|---|
| 1 | 8 | Três processos na mesma árvore, enxergando os mesmos PIDs, a mesma rede e o mesmo sistema de arquivos |
| 2 | 10 | Caixas de namespace se fechando uma a uma ao redor do processo, e o que ele deixa de enxergar a cada fechamento |
| 3 | 11 | Barra de memória subindo, batendo no teto do cgroup e sendo cortada |
| 4 | 14 | `docker run` ponta a ponta: CLI, daemon, consulta ao registry, pull das camadas, container de pé |
| 5 | 17 | Camadas empilhando de baixo para cima, com a camada gravável em destaque no topo |
| 6 | 25 | Primeiro build acendendo todas as camadas, segundo build reaproveitando cache e acendendo só a última |
| 7 | 33 | Artefato saltando do estágio builder para o runtime, e o builder desaparecendo |
| 8 | 42 | Dois containers na mesma rede, um resolvendo o outro pelo nome e trocando mensagem |
| 9 | 46 | Camadas subindo para o registry, com a tag sendo aplicada |

### Quizzes

Os três enunciados vêm do `PLANEJAMENTO_AULA_A_AULA.md` e não mudam: vantagem do
build multi-stage; diferença entre volume e bind mount; o que acontece com os
dados quando o container é destruído sem volume. Markup conforme o
`construtor-aulas`, com `quiz1Timer`, `quiz2Timer` e `quiz3Timer`, e o QR de
votação como placeholder tracejado, conforme a ADR-001.

---

## 6. Lab kit

Repositório: `josercf/mwe-2026-2-lab03-docker`. O aluno faz **fork**, nunca clone.

```
.devcontainer/
  devcontainer.json      docker-in-docker + feature de node, porque o gateway é Node
  post-create.sh         Ollama com qwen3.5:2b, binário do docker agent
  post-start.sh
.agents/skills/
  logitech-dockerfile/SKILL.md    skill pronta, usada na demonstração e na etapa 8
agente.yaml              configuração do docker agent, provedor definido após smoke test
ai/ask.py
servicos/
  coletor/server_telemetry.py     cópia congelada do gabarito da Aula 02
  gateway/server.js, package.json, public/index.html
etapas/
  01-isolamento/RESPOSTAS.md
  02-imagem/RESPOSTAS.md
  ... até 07-registry/RESPOSTAS.md
  08-bonus/RESPOSTAS.md
baseline/
  Dockerfile.coletor.ingenuo        estágio único, base full, para medir a redução
  Dockerfile.gateway.ingenuo
resgate/
  Dockerfile.coletor.minimo
  Dockerfile.gateway.minimo
docs/EVIDENCIAS.md
verificar.py
README.md
```

### O diretório `resgate/`

Atividade progressiva tem um risco que a monolítica não tem: travar na etapa 3
mata as etapas 4 a 7. O `resgate/` contém o Dockerfile mínimo funcional de cada
serviço. Quem usa **registra em `docs/EVIDENCIAS.md` que usou**, e o professor
enxerga isso na correção. Isso preserva a honestidade do entregável sem deixar
ninguém parado por uma hora.

### Verificador progressivo

`verificar.py --etapa N` valida só a etapa N. Sem argumento, valida as sete e
imprime o placar. Critérios:

| Etapa | Critério objetivo |
|---|---|
| 1 | `etapas/01-isolamento/RESPOSTAS.md` com os quatro valores pedidos, preenchidos |
| 2 | `etapas/02-imagem/RESPOSTAS.md` traz o `docker ps` do coletor rodando sobre `python:3.13-alpine` sem Dockerfile, e a prova de que o arquivo escrito na camada gravável sumiu após o `docker rm` |
| 3 | `Dockerfile.coletor` builda e o container resultante responde |
| 4 | Os dois Dockerfiles têm no mínimo 2 estágios e um `USER` não-root, e a redução contra a baseline de `Dockerfile.<servico>.ingenuo` é de no mínimo 80% |
| 5 | Volume `logitech-telemetria` existe e o arquivo de telemetria sobrevive a `docker rm` |
| 6 | Rede `logitech-net` existe e o gateway resolve o coletor pelo nome |
| 7 | `docs/EVIDENCIAS.md` traz a URL pública no Docker Hub e o manifesto responde |

### Entregáveis, com número

1. `Dockerfile.coletor` e `Dockerfile.gateway`, cada um com **no mínimo 2
   estágios** e um `USER` não-root.
2. Redução de **no mínimo 80%** no tamanho de cada imagem em relação à baseline,
   e imagem final do coletor **abaixo de 100 MB**. A baseline não é escolhida
   pelo aluno: são os `baseline/Dockerfile.<servico>.ingenuo` que o repositório
   entrega, de estágio único e base full, que o aluno builda na etapa 4 antes de
   escrever o multi-stage. Sem baseline fixa, o percentual não significa nada.
3. Volume nomeado `logitech-telemetria` com o arquivo de telemetria persistindo
   após `docker rm` do container.
4. Rede `logitech-net` com o gateway alcançando o coletor pelo nome.
5. `docs/EVIDENCIAS.md` com **7 valores numéricos**: tamanho ingênuo e final de
   cada uma das duas imagens, o percentual de redução de cada uma, e a memória em
   MB do coletor observada no `docker stats`.
6. Imagem publicada em `<usuario>/logitech-coletor:1.0`, pública, com a URL no
   README.
7. `verificar.py` imprimindo 7 de 7.
8. Bônus: `etapas/08-bonus/RESPOSTAS.md` com o Dockerfile que a skill gerou e
   **o que o agente errou e você corrigiu**.

**Um commit por etapa**, no padrão `feat(etapa-N): ...`, para que a progressão
fique visível no histórico. Isso reaproveita o Git das Aulas 01 e 02.

Entrega no formulário `https://forms.cloud.microsoft/r/LnU2cEXXHQ`, embutido no
slide 52 e citado no README.

### Por que o entregável muda em relação ao plano

O `PLANO_DE_ENSINO.md` pede imagem abaixo de 100 MB para os dois serviços. Para o
coletor Python isso é folgado, porque `python:3.13-alpine` fica perto de 55 MB.
Para o gateway Node não é alcançável sem distroless ou binário estático, porque
`node:22-alpine` sozinho já passa de 150 MB. Por isso o critério principal passou
a ser percentual de redução, e o valor absoluto de 100 MB foi mantido só onde é
honesto, no coletor.

---

## 7. Agent Skills

Três slides, do 48 ao 50, mais demonstração ao vivo do professor gerando o
`Dockerfile.gateway` pela skill.

O conteúdo conceitual: uma skill é instrução especializada que o agente carrega
**sob demanda**, quando a descrição casa com a tarefa, e não contexto colado no
prompt. O `SKILL.md` tem frontmatter com `name` e `description`, que é o que vai
para o prompt do agente, e um corpo que só é lido quando a skill é acionada.

O ponto pedagógico do slide 50: **o mesmo arquivo serve três agentes**. A
descoberta acontece em `.claude/skills/`, `.github/skills/`, `.agents/skills/` e
`~/.agents/skills/`, então a skill escrita para o `docker agent` funciona
igualmente no Claude Code e no Copilot. Isso amarra no `josercf/skill-library` e
na skill de code review introduzida na Aula 02.

O `docker agent` é Apache-2.0, vem pronto no Docker Desktop 4.63 ou superior, e
em Linux é binário do GitHub Releases com symlink em
`~/.docker/cli-plugins/docker-agent`. O `post-create.sh` do lab03 passa a
instalá-lo.

### Provedor de modelo: a decidir por teste

**Nada aqui está verificado ainda.** A ordem de tentativa, com o resultado a ser
registrado neste spec antes de o deck ser escrito:

1. **GitHub Models** pelo endpoint compatível com OpenAI, usando o `GITHUB_TOKEN`
   que o Codespaces injeta. É o mesmo caminho que o `ai/ask.py` já usa.
2. **Ollama local** com `qwen3.5:2b`, pelo endpoint compatível com OpenAI em
   `http://localhost:11434/v1`.
3. **Copilot do Codespaces** lendo o mesmo `SKILL.md`. Caminho garantido, sem
   `docker agent`, usado se 1 e 2 falharem.

---

## 8. Troca do modelo local

O `qwen2.5:1.5b` atual não aparece na lista de modelos com capacidade de `tools`
do Ollama. O lab03 passa a `qwen3.5:2b`, de 2,7 GB, que aparece.

O Gemma 4 foi avaliado e descartado por tamanho: a menor variante no Ollama é
`gemma4:e2b`, com 7,2 GB, contra 8 GB de RAM da máquina padrão do Codespaces,
disputados na Aula 03 com o Docker-in-Docker e com os containers que o próprio
aluno sobe. Os 2B do E2B são parâmetros efetivos, mas os pesos completos precisam
ser carregados.

A troca vale **apenas para o lab03 nesta entrega**. Propagar para os outros 12
laboratórios é tarefa separada, fora do caminho crítico de 18/08, porque exige
regenerar e ressincronizar 13 repositórios, e os alunos que já forkaram os labs
01 e 02 não receberiam a mudança de qualquer forma.

---

## 9. Documentos que mudam junto

| Arquivo | Mudança |
|---|---|
| `PLANEJAMENTO_AULA_A_AULA.md` | Agenda da Aula 03 reescrita nos 7 ciclos; entregável atualizado |
| `PLANO_DE_ENSINO.md` | Entregável da Aula 03 e o critério de tamanho de imagem |
| `docs/adrs/ADR-004-formato-progressivo-da-aula-03.md` | Novo, cobrindo D1, D5 e D6 |
| `aulas-1sem/index.html` | Card da Aula 03 apontando para o deck e o lab |
| `tools/scaffold_labs.py` | Entrega do lab03 sem `docker-compose.yml`, que é Aula 07; feature de node no lab03; modelo `qwen3.5:2b` |
| `docs/ANDAMENTO.md` | Estado da Aula 03 e pendências novas |
| `josercf/mwe-2026-2-lab03-docker` | Sincronização manual, preservando `.devcontainer/` e `ai/ask.py`. Não há `gabarito/` nesta aula: o que faz esse papel é o `resgate/`, e ele **vai** para o repositório do aluno por design |

---

## 10. Riscos abertos

| Risco | Mitigação |
|---|---|
| O `docker agent` pode não falar com o GitHub Models no devcontainer | Smoke test antes de escrever o deck, com dois níveis de fallback definidos na seção 7 |
| O `qwen3.5:2b` pode não sustentar o loop de tool calling | Mesmo smoke test; se falhar, a demonstração vai no Copilot e o `agente.yaml` fica documentado como exercício de casa |
| A redução de 80% pode não se confirmar na medição real | Medir os quatro tamanhos de verdade antes de fixar o critério no README, e ajustar o número se necessário |
| Sete atividades em 3,5 h é apertado | Ordem de corte definida na seção 3; cronometrar na primeira aplicação |
| Aluno sem conta no Docker Hub trava no ciclo 7 | Pré-requisito anunciado pelo professor antes da aula, repetido no slide 5 e no README |
| Atividade progressiva propaga travamento entre etapas | Diretório `resgate/`, com uso registrado em `EVIDENCIAS.md` |
| A máquina padrão do Codespaces pode não aguentar Ollama, Docker-in-Docker e containers ao mesmo tempo | Testar o lab inteiro dentro do devcontainer real antes de publicar; se apertar, o Ollama só sobe sob demanda no `post-start.sh` |

---

## 11. Pendências do professor

- Avisar a turma, antes de 18/08, para criar e verificar a conta no Docker Hub.
- Confirmar se a demonstração de Agent Skills será feita com a conta dele ou com
  o caminho do aluno, caso o smoke test do GitHub Models falhe.
