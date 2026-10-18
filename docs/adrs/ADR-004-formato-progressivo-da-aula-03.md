# ADR-004: Formato progressivo, Agent Skills e modelo local na Aula 03

- **Data:** 2026-07-30
- **Status:** Aceita
- **Decisores:** Prof. José Romualdo da Costa Filho
- **Relacionadas:** ADR-002 e ADR-003, que trataram do escopo do laboratório da
  Aula 02 e cujo entregável é o insumo desta aula.

## Contexto

A Aula 03, de 18/08/2026, é a última do Módulo I antes do CP1, uma prova prática
individual que cobra conteinerização. A turma chega com conhecimento zero de
containers e o professor pediu uma visão de 360 graus do tema, do isolamento de
processos no Linux até a publicação de imagem em registry público.

O padrão do acervo, consolidado nas Aulas 01 e 02 e descrito em
`aulas-1sem/SKILL.md`, concentra a prática em um laboratório único de 60 minutos
no Bloco 2. O professor pediu explicitamente outra coisa para esta aula:
atividade a cada etapa, progressiva, individual, com entrega de um repositório
único no fim.

Três decisões desta aula divergem de documentos já aprovados e por isso ficam
registradas aqui.

## Decisões

### 1. A aula se organiza em sete ciclos de teoria curta seguida de prática

O bloco teórico contínuo de 40 minutos previsto no
`PLANEJAMENTO_AULA_A_AULA.md` é dissolvido. A aula passa a ter sete ciclos, cada
um com 8 a 12 minutos de teoria e 6 a 10 minutos de prática individual:
isolamento de processos, imagem e camadas, Dockerfile e build, multi-stage,
volumes, network e observação, registry e Docker Hub.

Os três quizzes e o intervalo de 30 minutos às 20h50 permanecem nos horários
oficiais. A agenda da Aula 03 no `PLANEJAMENTO_AULA_A_AULA.md` é reescrita para
refletir isso.

### 2. Agent Skills entram como demonstração, não como oitavo ciclo

O professor pediu a apresentação das Agent Skills do Docker para que os alunos
usem IA para manipular containers e construir imagens. Elas entram em três
slides no encerramento, mais uma demonstração ao vivo, e viram etapa 8 bônus no
laboratório, feita em casa.

Não viram ciclo com prática em sala porque isso exigiria rebaixar o ciclo de rede
a demonstração, e porque 30 alunos disparando agente ao mesmo tempo estouraria a
cota do free tier do GitHub Models. O `docker agent` é Apache-2.0 e passa a ser
instalado pelo `post-create.sh` do lab03.

### 3. O modelo local do lab03 passa a ser `qwen3.5:2b`

O `qwen2.5:1.5b`, usado hoje como fallback local do `ai/ask.py` nos 13
laboratórios, não consta na lista de modelos com capacidade de `tools` do Ollama,
o que o torna um plano B fraco para a demonstração de agente.

O Gemma 4, avaliado a pedido do professor, tem function calling nativo e licença
Apache-2.0, mas foi descartado por tamanho: a menor variante no Ollama,
`gemma4:e2b`, ocupa 7,2 GB, contra 8 GB de RAM da máquina padrão do Codespaces,
disputados na Aula 03 com o Docker-in-Docker e com os containers que o aluno
sobe. Os 2B do E2B são parâmetros efetivos, mas os pesos completos precisam ser
carregados na memória.

A troca vale **apenas para o lab03 nesta entrega**.

## Motivações

- **Todo aluno pratica.** A atividade é individual e acontece sete vezes na
  noite, em vez de uma. Uma semana antes de uma prova prática individual, isso
  importa mais do que a conveniência da agenda.
- **Erro conceitual aparece cedo.** Quem entendeu camadas errado descobre no
  ciclo 2, e não às 22h30 com o laboratório inteiro travado.
- **A entrega vira uma trilha.** Um commit por etapa deixa a progressão visível
  no histórico e reaproveita o Git das Aulas 01 e 02.
- **A skill escrita é portátil.** O mesmo `SKILL.md` é descoberto em
  `.claude/skills/`, `.github/skills/` e `.agents/skills/`, então serve Claude
  Code, Copilot e `docker agent`, o que amarra no `josercf/skill-library`.

## Riscos conhecidos

| Risco | Mitigação |
|---|---|
| Travar em uma etapa mata as seguintes | Diretório `resgate/` no lab, com Dockerfile mínimo por serviço; quem usa registra em `docs/EVIDENCIAS.md` |
| Sete atividades não cabem em 3,5 h | Ordem de corte definida: primeiro o ciclo de rede vira demonstração, depois a segunda metade do ciclo de volumes. Registry e Agent Skills nunca saem |
| Aluno sem conta no Docker Hub trava no ciclo 7 | Pré-requisito anunciado pelo professor antes da aula, repetido em slide próprio e no README |
| O provedor de modelo do `docker agent` pode não funcionar no Codespaces | Smoke test antes de o deck ser escrito, com dois níveis de fallback: Ollama local e, por último, Copilot lendo o mesmo `SKILL.md` |
| Ollama, Docker-in-Docker e containers competindo por 8 GB | Testar o lab inteiro no devcontainer real; se apertar, o Ollama sobe sob demanda |

## Consequências

**Positivas.** Todo aluno executa cada conceito logo depois de vê-lo. O
entregável final é um repositório com trilha de commits auditável e sete
critérios objetivos verificados por script. A aula cobre o tema em 360 graus sem
invadir o escopo da Aula 07.

**Negativas.** A Aula 03 deixa de seguir o padrão de agenda das Aulas 01 e 02, o
que cria uma exceção no acervo e no `aulas-1sem/SKILL.md`. O aluno conteineriza
uma cópia congelada dos serviços da Aula 02, e não o próprio código, o que
enfraquece a continuidade da espiral em troca de um ponto de partida
determinístico. E o lab03 passa a divergir dos outros 12 no modelo local, até que
a propagação seja feita.

## Pendente de verificação

Nada sobre o provedor de modelo do `docker agent` foi testado até a aceitação
desta ADR. O resultado do smoke test deve ser registrado em
`docs/superpowers/specs/2026-07-30-aula03-docker-design.md`, seção 7, antes de o
deck ser escrito.
