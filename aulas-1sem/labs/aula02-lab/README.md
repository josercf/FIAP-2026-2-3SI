# Laboratório Prático - Aula 02

## Disciplina: Microservice and Web Engineering & IT Services
**Prof.º José Romualdo | FIAP Sistemas de Informação**

### Case: LogiTech Enterprise AI Platform (Fase 2 - Camada de Aplicação)

Na Aula 01 vocês entregaram a **especificação**: `docs/PRD.md` e `docs/SDD.md` do
serviço de telemetria, com Bounded Contexts, Linguagem Ubíqua e a escolha de TCP
ou UDP justificada por requisito não funcional.

Hoje se implementa o **UC03 do PRD**: expor a telemetria dos 400 caminhões para
os operadores logísticos. O coletor de sockets L4 já vem pronto neste
repositório; o que vocês escrevem é a camada HTTP/SSE por cima dele.

**Duração:** 60 minutos, em dupla.

---

## Por que o coletor de sockets vem pronto

Implementar os sockets a partir do SDD, subir para HTTP, inspecionar o tráfego e
conduzir um Pull Request não cabe em 60 minutos. O objetivo desta aula é a
**camada de aplicação** e o **fluxo de revisão de código**, então é neles que o
tempo é gasto. `sockets-l4/` é ponto de partida, não tarefa.

Leiam o código do coletor mesmo assim: ele é a materialização do diagrama de
comunicação L4 do SDD de vocês, e o Passo 2 depende de entender o que ele grava.

---

## Estrutura do repositório

```
sockets-l4/
  server_telemetry.py     coletor pronto: UDP 8081 (GPS) e TCP 8080 (entregas)
  client_telemetry.py     simulador da frota
http-l7/
  server.js               ESQUELETO: os TODO desta aula são aqui
  verificar.mjs           autoavaliação dos critérios de aceitação
  package.json
  public/index.html       painel do operador, consome o SSE, já pronto
docs/
  OBSERVACOES.md          template das três medições
data/                     criado em tempo de execução pelo coletor
```

---

## Pré-requisitos

- Python 3.9 ou superior (só a biblioteca padrão, sem `pip install`).
- Node.js 18 ou superior (só módulos nativos, sem `npm install`).
- `curl` na linha de comando.

Tudo isso já vem no devcontainer do Lab Kit. Em Codespaces, nada precisa ser
instalado.

---

## Passo 1: Fork e branch (5 min)

1. Fork do Lab Kit `josercf/mwe-2026-2-lab02-http-sse`.
2. Renomeie o fork para `mwe-2026-2-lab02-duplaXX`, com dois dígitos.
3. Em **Settings > Collaborators**, adicione o colega, o professor e a **dupla
   vizinha**, que fará a revisão do Pull Request.
4. Clone e crie a branch:

```bash
git clone https://github.com/SEU-USUARIO/mwe-2026-2-lab02-duplaXX.git
cd mwe-2026-2-lab02-duplaXX
git switch -c feature/http-telemetry
git branch --show-current
```

A partir de hoje **nada é comitado direto na `main`**.

---

## Passo 2: Subir o coletor de sockets da Aula 01 (8 min)

Dois terminais.

```bash
# Terminal 1: o coletor L4
python3 sockets-l4/server_telemetry.py

# Terminal 2: a frota simulada
python3 sockets-l4/client_telemetry.py --caminhoes 5 --intervalo 1
```

Confira antes de seguir:

```bash
wc -l data/telemetria.jsonl   # rode duas vezes, com alguns segundos entre elas
```

O número precisa estar crescendo. Se o arquivo não existe ou não cresce, o Passo
3 não terá o que transmitir.

> **Simplificação assumida:** a passagem do coletor para a API é por arquivo
> (`data/telemetria.jsonl`), de propósito, para manter o laboratório previsível
> em 60 minutos. Da Aula 07 em diante isso vira comunicação entre containers.

---

## Passo 3: Escrever o servidor HTTP/SSE (27 min) - esta é a parte avaliada

Abra `http-l7/server.js`. O esqueleto sobe e responde; `GET /health` está
completo e serve de modelo. Complete os quatro `TODO`:

| Rota | O que deve devolver | Exigência mínima |
|---|---|---|
| `GET /health` | Status do serviço | Pronto. 200, JSON, campo `uptime` em segundos |
| `GET /api/v1/posicoes` | Última posição de cada caminhão | 200, array com **no mínimo 5** objetos, `Cache-Control: max-age=5` |
| `GET /api/v1/eventos` | Stream SSE | `text/event-stream`, `no-cache`, `retry: 3000`, campos `id`, `event` e `data`, **1 evento a cada 2 s no máximo** |
| verbo errado | Erro correto | **405** com header `Allow: GET` |
| rota inexistente | Erro correto | **404** com corpo JSON. Nunca 200 com `{"erro": ...}` |

```bash
node http-l7/server.js
# painel do operador: http://localhost:3000
```

Antes de abrir o Pull Request:

```bash
node http-l7/verificar.mjs
```

O script checa os sete critérios (CA-01 a CA-07) e imprime o que falta. **Pull
Request com verificação vermelha não passa na revisão.**

---

## Passo 4: Medir o serviço com cURL (10 min)

Preencha `docs/OBSERVACOES.md` com **três respostas numéricas**:

| # | Pergunta | Comando |
|---|---|---|
| O-01 | Quantos headers a resposta de `/api/v1/posicoes` traz, e quais? | `curl -i` |
| O-02 | Quantos ms até a conexão, e quantos até a resposta completa? | `curl -w "%{time_connect} %{time_total}"` |
| O-03 | Qual o intervalo medido entre dois eventos SSE consecutivos? | `curl -N` |

**Experimento obrigatório:** apaguem a linha em branco depois do `data:`,
reiniciem o servidor e observem. Os bytes continuam saindo no `curl -N`, mas o
painel do navegador para de atualizar. Registrem o que mudou e devolvam o `\n\n`
ao lugar.

Resposta sem número não conta como resposta.

---

## Passo 5: Pull Request e Code Review cruzado (10 min)

```bash
git add http-l7/ docs/OBSERVACOES.md
git commit -m "feat(api): expoe posicoes da frota via HTTP"
git commit -m "feat(sse): transmite posicoes novas por SSE"
git push -u origin feature/http-telemetry
```

Abra o Pull Request de `feature/http-telemetry` para `main`, com:

- no mínimo **2 commits** em Conventional Commits;
- descrição com **3 seções**: o que mudou, como testar, o que ficou de fora.

A **dupla vizinha** revisa e precisa deixar:

- no mínimo **2 comentários em linha**, cada um apontando linha, efeito e sugestão;
- **1 aprovação** registrada em *Review*.

Merge só depois da aprovação. Quem aprova sem ler responde pelo que passou.

---

## Critérios de aceitação

| # | Critério | Verificado por |
|---|---|---|
| CA-01 | `GET /health` devolve 200 JSON com `uptime` numérico | `verificar.mjs` |
| CA-02 | `GET /api/v1/posicoes` devolve 200, array com 5 ou mais caminhões e `Cache-Control` com `max-age` | `verificar.mjs` |
| CA-03 | `GET /api/v1/eventos` devolve 200 com `text/event-stream` e `no-cache` | `verificar.mjs` |
| CA-04 | O stream entrega ao menos 2 eventos terminados em linha em branco | `verificar.mjs` |
| CA-05 | Os eventos trazem `retry`, `id`, `event` e `data` | `verificar.mjs` |
| CA-06 | Rota desconhecida devolve 404 | `verificar.mjs` |
| CA-07 | `POST` em rota de leitura devolve 405 | `verificar.mjs` |
| CA-08 | `docs/OBSERVACOES.md` com as três medições numéricas preenchidas | Revisão |
| CA-09 | Pull Request com 2 ou mais commits semânticos e descrição em 3 seções | Revisão |
| CA-10 | Revisão da dupla vizinha com 2 ou mais comentários e 1 aprovação | Revisão |
| CA-11 | Nomes de campo JSON coerentes com a Linguagem Ubíqua do SDD da dupla | Revisão |

---

## Como entregar

Submeta a **URL do Pull Request** no formulário da Aula 02, no formato:

```
https://github.com/SEU-USUARIO/mwe-2026-2-lab02-duplaXX/pull/1
```

**Formulário:** <https://forms.cloud.microsoft/r/ykGYKsPAj7>

Um envio por dupla, identificando os dois integrantes e a dupla revisora, até o
fim da aula.

> Não utilizem o formulário da Aula 01: ele coleta a entrega de PRD e SDD e não
> serve para esta atividade.

---

## Autoavaliação antes de entregar

| Pergunta | Sim / Não |
|---|---|
| `node http-l7/verificar.mjs` termina sem falha? | |
| O painel em `http://localhost:3000` atualiza sozinho, sem F5? | |
| Fechar a aba do painel encerra o observador no servidor (sem vazamento)? | |
| As três observações têm número medido, e não texto genérico? | |
| Os nomes dos campos JSON são os mesmos do glossário do seu SDD? | |
| O Pull Request explica como testar sem que o revisor precise perguntar? | |

---

## Na próxima aula

A Aula 03 empacota estes dois serviços, o coletor Python e o gateway Node.js, em
imagens Docker multi-stage com menos de 100 MB, e é aí que a passagem por arquivo
entre eles começa a ser substituída.
