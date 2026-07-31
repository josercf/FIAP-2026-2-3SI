# Laboratório Prático - Aula 03

## Disciplina: Microservice and Web Engineering & IT Services
**Prof.º José Romualdo | FIAP Sistemas de Informação**

### Case: LogiTech Enterprise AI Platform (Fase 3, Conteinerização)

Na Aula 02 vocês entregaram dois serviços funcionando soltos na máquina: o
coletor de telemetria em Python e o gateway HTTP/SSE em Node.js. Os dois
continuam rodando "na minha máquina", com tudo instalado à mão, e é
exatamente esse o problema desta aula.

Hoje esses dois serviços viram imagem Docker: primeiro vocês isolam um
processo comum para entender o que um container realmente é, depois
conteinerizam o coletor e o gateway em Dockerfiles multi-stage com menos de
100 MB, e por fim publicam a imagem final num registry público.

**Atividade individual**, sete etapas progressivas, uma prática curta depois
de cada bloco de teoria. Um commit por etapa.

---

## O que já vem pronto, e o que vocês fazem

| Vem pronto, é modelo | Vocês escrevem |
|---|---|
| `servicos/coletor/server_telemetry.py`, o coletor da Aula 02, congelado | `Dockerfile.coletor` e `Dockerfile.gateway`, multi-stage, na raiz |
| `servicos/gateway/`, o gateway da Aula 02, congelado | Os oito `RESPOSTAS.md`, um por etapa, e `docs/EVIDENCIAS.md` |
| `baseline/Dockerfile.<servico>.ingenuo`, o ponto de partida da medição | O volume `logitech-telemetria` e a rede `logitech-net` |
| `resgate/Dockerfile.<servico>.minimo`, a rede de segurança para quem travar | A imagem publicada no seu Docker Hub |
| `verificar.py`, a autoavaliação progressiva | Um commit por etapa concluída |

Os dois serviços **não são tarefa**: não editem
`servicos/coletor/server_telemetry.py` nem os arquivos de
`servicos/gateway/`. O caminho de dados deles é relativo por padrão
(`dados/telemetria.jsonl`, resolvido a partir da raiz do laboratório); é o
Dockerfile que vocês escrevem quem fixa o caminho absoluto dentro do
container, com `ENV LOGITECH_DADOS=/dados/telemetria.jsonl`.

---

## Pré-requisitos

> **Conta no Docker Hub, criada e verificada por e-mail, antes da aula.** A
> etapa 7 publica uma imagem lá, e a verificação de e-mail sozinha custa de 5
> a 10 minutos. Sem conta pronta, vocês travam no ciclo mais tardio da noite.

Além disso:

- Fork do repositório `josercf/mwe-2026-2-lab03-docker` (nunca clone direto).
- GitHub Codespaces, ou Docker Desktop local com pelo menos 8 GB de RAM
  livres para o devcontainer, o Docker-in-Docker e os containers que vocês
  vão subir ao longo da aula.

Tudo o resto (Python, Node, Docker, Ollama com o modelo local) já vem no
devcontainer do laboratório.

---

## Como abrir o Codespace

1. Fork de `josercf/mwe-2026-2-lab03-docker` para a sua conta.
2. No fork, **Code > Codespaces > Create codespace on main**.
3. Aguarde o `post-create.sh` terminar: ele sobe o Ollama, baixa o modelo
   local e instala o `docker-agent` usado na etapa bônus.
4. Confirme que o Docker responde:

```bash
docker version
docker run --rm hello-world
```

Se preferir rodar local em vez de Codespaces, a imagem do devcontainer é
`mcr.microsoft.com/devcontainers/python:1-3.12-bookworm`.

---

## As sete etapas

Cada etapa tem um roteiro completo em `etapas/NN-nome/RESPOSTAS.md`: o
enunciado, o comando exato a rodar e os campos a preencher. Esta seção é o
resumo; o roteiro completo mora no arquivo de cada etapa.

### Etapa 1, Isolamento de processos (`etapas/01-isolamento/`)

Suba um `alpine` comum e compare o PID do mesmo processo visto de dentro do
container e visto do host (`docker inspect -f '{{.State.Pid}}' ...`).
Registre `PID_DENTRO`, `PID_FORA`, `HOSTNAME_DENTRO` e `ENTRADAS_PROC_DENTRO` no
próprio `RESPOSTAS.md` da etapa.

### Etapa 2, Imagem, camadas e efemeridade (`etapas/02-imagem/`)

Rode o coletor sem Dockerfile nenhum, sobre `python:3.12-alpine`, com bind
mount do código-fonte. Escreva um arquivo na camada gravável, destrua o
container, e prove que o arquivo sumiu. Registre `CONTAINER_ID` e
`ARQUIVO_APOS_RM` no `RESPOSTAS.md` da etapa.

### Etapa 3, Dockerfile e build (`etapas/03-dockerfile/`)

Escreva `Dockerfile.coletor` do zero, na raiz do laboratório, e confirme que
ele builda de verdade (`docker build -f Dockerfile.coletor -t
verificar-coletor:etapa3 .`). Sem marcador numérico nesta etapa.

### Etapa 4, Multi-stage (`etapas/04-multistage/`)

Builda a baseline ingênua de `baseline/`, mede o tamanho, escreve
`Dockerfile.coletor` e `Dockerfile.gateway` multi-stage na raiz (mínimo dois
estágios `FROM`, `USER` não-root), mede de novo. Registre os seis valores
em `docs/EVIDENCIAS.md`: os quatro tamanhos e os dois percentuais de
redução, mínimo de 80% para cada serviço.

### Etapa 5, Volumes (`etapas/05-volumes/`)

Crie o volume `logitech-telemetria`, suba o coletor com ele montado, mande
telemetria de verdade, destrua o container e confirme, com outro container
do zero, que os dados sobreviveram. Registre `LINHAS_APOS_RM` em
`docs/EVIDENCIAS.md`.

### Etapa 6, Network e observação (`etapas/06-network/`)

Crie a rede `logitech-net`, suba coletor e gateway nela, prove que o
gateway resolve o coletor pelo nome, e leia o consumo de memória do coletor
com `docker stats`. Registre `MEMORIA_COLETOR_MB` em `docs/EVIDENCIAS.md`.

### Etapa 7, Registry e Docker Hub (`etapas/07-registry/`)

Publique a imagem final do coletor no seu Docker Hub, pública, e confirme
que ela responde sem sessão aberta (`docker manifest inspect`). Registre
`IMAGEM_PUBLICA` em `docs/EVIDENCIAS.md`, no formato `usuario/imagem:tag`.

---

## Etapa 8, bônus: Agent Skill

Sem prazo de aula, feita em casa. Peça para o agente escrever um Dockerfile
usando a skill `logitech-dockerfile` (`docker-agent run agente.yaml`), cole
o resultado em `etapas/08-bonus/RESPOSTAS.md` e escreva, em pelo menos duas
frases, o que ele errou e como vocês corrigiram. O modelo local do
laboratório é bem menor que o usado na demonstração em sala; errar faz parte
do exercício, o que conta é reconhecer o erro.

---

## Critérios de aceitação

A tabela abaixo espelha, etapa por etapa, o que `verificar.py` confere.

| # | Critério | Verificado por |
|---|---|---|
| CA-01 | `etapas/01-isolamento/RESPOSTAS.md` com os quatro marcadores preenchidos, PIDs plausíveis e diferentes | `verificar.py --etapa 1` |
| CA-02 | `etapas/02-imagem/RESPOSTAS.md` com `CONTAINER_ID` real e `ARQUIVO_APOS_RM`; imagem `python:3.12-alpine` presente localmente | `verificar.py --etapa 2` |
| CA-03 | `Dockerfile.coletor` na raiz do laboratório, buildando sem erro | `verificar.py --etapa 3` |
| CA-04 | `Dockerfile.coletor` e `Dockerfile.gateway` com no mínimo 2 estágios `FROM` e `USER` não-root, os dois buildando; `REDUCAO_COLETOR` e `REDUCAO_GATEWAY` >= 80% em `docs/EVIDENCIAS.md` | `verificar.py --etapa 4` |
| CA-05 | Volume `logitech-telemetria` existe; `LINHAS_APOS_RM` em `docs/EVIDENCIAS.md` | `verificar.py --etapa 5` |
| CA-06 | Rede `logitech-net` existe; `MEMORIA_COLETOR_MB` em `docs/EVIDENCIAS.md` | `verificar.py --etapa 6` |
| CA-07 | `IMAGEM_PUBLICA` em `docs/EVIDENCIAS.md`, respondendo de verdade a `docker manifest inspect` | `verificar.py --etapa 7` |
| CA-08 | `etapas/08-bonus/RESPOSTAS.md` com o Dockerfile gerado pela skill e `O_QUE_O_AGENTE_ERROU` com no mínimo duas frases | Correção do professor |

Rode a suíte inteira, ou uma etapa isolada, a qualquer momento:

```bash
python3 verificar.py             # roda as sete etapas
python3 verificar.py --etapa 4   # roda só uma etapa
```

### O que a máquina prova, e o que fica por sua conta

Este laboratório é progressivo, e a etapa 2 é justamente sobre efemeridade:
quando `verificar.py` roda, o container que gerou a evidência daquela etapa
**já não existe mais**. Nem todo critério dá para provar por máquina. A
tabela abaixo é a régua real: onde o `verificar.py` de fato confirma algo no
Docker da sua máquina, e onde ele só confere que o texto tem a forma certa,
confiando no que você escreveu.

| Etapa | Verificado por máquina | Declarado por você (sem checagem de máquina possível) |
|---|---|---|
| 1. Isolamento de processos | `PID_DENTRO` e `PID_FORA` são números, diferentes entre si e plausíveis (`PID_DENTRO` até 50, `PID_FORA` a partir de 100); `HOSTNAME_DENTRO` tem o formato de hostname que o Docker gera sozinho (12 caracteres hexadecimais) | Que os valores vieram de um container real: o container já não existe quando o verificador roda. `ENTRADAS_PROC_DENTRO` só confere presença de um valor não vazio, sem checagem de formato |
| 2. Imagem, camadas e efemeridade | Que a imagem `python:3.12-alpine` está presente localmente, via `docker image inspect` de verdade; `ARQUIVO_APOS_RM` é `sumiu` ou `ausente`; `CONTAINER_ID` tem formato hexadecimal | Que o `CONTAINER_ID` citado corresponde de fato ao container que gerou aquela evidência, e que a prova de efemeridade é verdadeira e não só bem formatada: o container já foi destruído quando o verificador roda |
| 3. Dockerfile e build | `Dockerfile.coletor` builda de verdade via `docker build` | - |
| 4. Multi-stage | `Dockerfile.coletor` e `Dockerfile.gateway` têm ao menos 2 instruções `FROM` e `USER` não-root cada um; os dois buildam de verdade | Os percentuais `REDUCAO_COLETOR`/`REDUCAO_GATEWAY`: o verificador confere que são números maiores ou iguais a 80%, mas não mede o tamanho de imagem sozinho, confia no que você mediu e registrou |
| 5. Volumes | O volume `logitech-telemetria` existe de verdade no Docker no momento em que o verificador roda | `LINHAS_APOS_RM`: inteiro positivo declarado por você; o verificador não confirma que aquele número corresponde ao que de fato sobreviveu ao `docker rm` |
| 6. Network e observação | A rede `logitech-net` existe de verdade no Docker no momento em que o verificador roda | `MEMORIA_COLETOR_MB`: número positivo declarado por você, lido de um `docker stats` que já não está mais rodando quando o verificador roda |
| 7. Registry e Docker Hub | `IMAGEM_PUBLICA` responde de verdade via `docker manifest inspect`, com mensagem diferenciando "imagem não existe ou está privada" de "registry inalcançável" | - |

Nas linhas onde a máquina não consegue provar tudo, o professor confere na
correção. Preencher com valor fabricado, sem ter feito o exercício, engana a
correção, não o `verificar.py`.

---

## Como entregar

**Um commit por etapa concluída**, no padrão Conventional Commits:

```bash
git add etapas/01-isolamento
git commit -m "feat(etapa-1): isolamento de processos"

git add etapas/02-imagem
git commit -m "feat(etapa-2): imagem, camadas e efemeridade"

git add Dockerfile.coletor etapas/03-dockerfile
git commit -m "feat(etapa-3): primeiro Dockerfile do coletor"

git add Dockerfile.coletor Dockerfile.gateway etapas/04-multistage docs/EVIDENCIAS.md
git commit -m "feat(etapa-4): multi-stage nos dois serviços"

git add docs/EVIDENCIAS.md etapas/05-volumes
git commit -m "feat(etapa-5): volume nomeado para a telemetria"

git add docs/EVIDENCIAS.md etapas/06-network
git commit -m "feat(etapa-6): rede dedicada e observação"

git add docs/EVIDENCIAS.md etapas/07-registry
git commit -m "feat(etapa-7): imagem publicada no Docker Hub"

# opcional, sem prazo de aula
git add etapas/08-bonus
git commit -m "feat(etapa-8): Dockerfile gerado pela Agent Skill"

git push
```

A progressão precisa ficar visível no histórico do seu fork: sete commits
(oito com o bônus), não um único commit final com tudo dentro.

Ao terminar, submeta a **URL do seu fork** no formulário:

**Formulário:** <https://forms.cloud.microsoft/r/LnU2cEXXHQ>

Um envio por aluno, até o fim da aula.

---

## O diretório `resgate/`

Atividade progressiva tem um risco que uma atividade única não tem: travar
na etapa 3 mata as etapas 4 a 7 inteiras. `resgate/` traz o Dockerfile
mínimo e funcional de cada serviço, multi-stage, com usuário não-root, pronto
para buildar.

Se você travar, copie o arquivo correspondente para a raiz, com o nome
final:

```bash
cp resgate/Dockerfile.coletor.minimo Dockerfile.coletor
```

E registre em `docs/EVIDENCIAS.md`, no campo `USEI_O_RESGATE`, que usou o
resgate e em qual etapa. Usar o resgate não reprova nenhum critério que o
`verificar.py` confirme por máquina, mas é informação que o professor
precisa ter na correção. Preferimos que você siga adiante com o resgate a
que fique travado a aula inteira numa etapa só.

---

## Na próxima aula

A Aula 04 é o CP1, prova prática individual cobrando conteinerização. A
Aula 07 retoma esta plataforma para introduzir o Docker Compose, orquestrando
coletor e gateway juntos, com a passagem por arquivo entre eles começando a
ser substituída por comunicação de verdade entre containers.
