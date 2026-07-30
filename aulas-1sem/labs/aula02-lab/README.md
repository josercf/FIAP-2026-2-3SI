# Laboratório Prático - Aula 02

## Disciplina: Microservice and Web Engineering & IT Services
**Prof.º José Romualdo | FIAP Sistemas de Informação**

### Case: LogiTech Enterprise AI Platform (Fase 2 - Camada de Aplicação)

Na Aula 01 vocês entregaram a **especificação**: `docs/PRD.md` e `docs/SDD.md` do
serviço de telemetria, com Bounded Contexts, Linguagem Ubíqua e a escolha de TCP
ou UDP justificada por requisito não funcional.

Hoje aquele desenho vira software: primeiro o **coletor L4** que vocês
especificaram, depois a **camada HTTP/SSE** por cima dele, e no fim o Pull
Request revisado pela dupla vizinha.

**Duração:** 72 minutos, em dupla.

---

## O que vocês escrevem, e o que já vem pronto

| Vem pronto, é modelo | Vocês escrevem |
|---|---|
| O lado **TCP** do coletor (`escutar_tcp`, `atender_conexao`) | O lado **UDP**: os quatro TODO de `escutar_udp` |
| O simulador da frota (`client_telemetry.py`) | O servidor HTTP/SSE (`http-l7/server.js`) |
| O painel do operador (`http-l7/public/`) | As três medições em `docs/OBSERVACOES.md` |
| Os dois verificadores | A revisão em `docs/CODE_REVIEW.md` |

O TCP pronto é o modelo do UDP: a diferença real é `SOCK_DGRAM` no lugar de
`SOCK_STREAM` e a ausência de `listen`, porque em UDP não há conexão a aceitar.
Leiam antes de escrever.

---

## Estrutura do repositório

```
sockets-l4/
  server_telemetry.py     TCP 8080 pronto; UDP 8081 são os TODO do Passo 2
  client_telemetry.py     simulador da frota, pronto
  verificar.py            autoavaliação do Passo 2
http-l7/
  server.js               ESQUELETO: os TODO do Passo 3 são aqui
  verificar.mjs           autoavaliação do Passo 3
  package.json
  public/index.html       painel do operador, consome o SSE, já pronto
docs/
  OBSERVACOES.md          template das três medições
  CODE_REVIEW.md          registro da revisão que vocês fizerem
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

## Passo 2: Completar o coletor de sockets do seu SDD (12 min)

Abram `sockets-l4/server_telemetry.py`. A função `escutar_tcp` está inteira e é
o modelo. Completem os quatro TODO de `escutar_udp`:

| TODO | O que fazer |
|---|---|
| 1 | Criar o socket UDP (`SOCK_DGRAM`), `SO_REUSEADDR` e `bind` na 8081 |
| 2 | O laço de recepção com `recvfrom(2048)` |
| 3 | `json.loads` do datagrama, descartando o ilegível sem derrubar o laço |
| 4 | Validar com `validar_posicao` e gravar com `anexar` |

**Por que UDP e não TCP:** está no SDD de vocês. Para posição de GPS, frescor
vale mais que completude: perder um datagrama é aceitável, porque em um segundo
vem outro mais novo. Esperar retransmissão, não.

Confiram com o verificador, que manda os datagramas sozinho:

```bash
# Terminal 1
python3 sockets-l4/server_telemetry.py

# Terminal 2
python3 sockets-l4/verificar.py
```

Ele checa cinco critérios (CA-L4-01 a CA-L4-05). Só sigam para o Passo 3 quando
passar nos cinco. Depois, para gerar tráfego contínuo:

```bash
python3 sockets-l4/client_telemetry.py --caminhoes 5 --intervalo 1
```

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

São **duas entregas**: o PR de vocês aprovado, e a revisão que vocês fizerem no
PR da dupla vizinha.

```bash
git add sockets-l4/ http-l7/ docs/
git commit -m "feat(l4): completa o coletor UDP de telemetria"
git commit -m "feat(sse): transmite posicoes novas por SSE"
git push -u origin feature/http-telemetry
```

Abra o Pull Request de `feature/http-telemetry` para `main`, com:

- no mínimo **2 commits** em Conventional Commits;
- descrição com **3 seções**: o que mudou, como testar, o que ficou de fora.

A **dupla vizinha** revisa e precisa deixar:

- no mínimo **2 comentários em linha**, cada um apontando linha, efeito e sugestão;
- **1 aprovação** registrada em *Review*.

E vocês fazem o mesmo no PR dela, registrando em `docs/CODE_REVIEW.md`: qual PR
revisaram, **como** revisaram, o que **encontraram** e qual **sugestão** deram.

Merge só depois da aprovação. Quem aprova sem ler responde pelo que passou.

### Revisão assistida pela skill de Code Review

Nossa biblioteca traz uma skill de revisão de código. Instalem uma vez:

```bash
git clone https://github.com/josercf/skill-library.git /tmp/skill-library
mkdir -p .claude/skills
cp -r /tmp/skill-library/skills/code-review .claude/skills/
```

E usem no diff da dupla vizinha:

```bash
git fetch origin feature/http-telemetry
git diff main...origin/feature/http-telemetry > /tmp/pr.diff

python ai/ask.py "$(cat .claude/skills/code-review/SKILL.md)

Revise este diff de um gateway HTTP/SSE em Node.js.
Para cada achado: arquivo e linha, o efeito, e a sugestao.

$(cat /tmp/pr.diff)"
```

Perguntas que rendem, porque pedem um caso concreto:

```bash
python ai/ask.py "Neste handler SSE, o que acontece quando o cliente
fecha a aba? O observador e removido, ou vaza?

$(cat http-l7/server.js)"

python ai/ask.py "Estes nomes de campo batem com o glossario do SDD?
Aponte cada divergencia.

CODIGO: $(cat http-l7/server.js)"
```

Perguntas que não rendem: *"este código está bom?"* devolve elogio genérico, e
*"corrija para mim"* devolve código que vocês não conseguem defender na revisão.

> **A skill não aprova o Pull Request e não assina por vocês.** Todo comentário
> postado precisa ser um comentário que vocês conseguem explicar. Se a IA
> apontou algo que vocês não entenderam, estudem até entender ou não postem. O
> `CODE_REVIEW.md` tem um campo para o que ela sugeriu e vocês **descartaram**,
> com a razão: descartar com justificativa é sinal de que leram o código.

---

## Critérios de aceitação

### Passo 2, o coletor L4

| # | Critério | Verificado por |
|---|---|---|
| CA-L4-01 | O coletor grava as posições recebidas em `data/telemetria.jsonl` | `sockets-l4/verificar.py` |
| CA-L4-02 | Cada linha do arquivo é um JSON válido, uma posição por linha | `sockets-l4/verificar.py` |
| CA-L4-03 | As posições trazem `placa`, `lat`, `lng` e `recebido_em` | `sockets-l4/verificar.py` |
| CA-L4-04 | Datagrama ilegível ou incompleto é descartado, não gravado | `sockets-l4/verificar.py` |
| CA-L4-05 | O coletor continua gravando depois de receber lixo | `sockets-l4/verificar.py` |

### Passo 3, a camada HTTP/SSE

| # | Critério | Verificado por |
|---|---|---|
| CA-01 | `GET /health` devolve 200 JSON com `uptime` numérico | `http-l7/verificar.mjs` |
| CA-02 | `GET /api/v1/posicoes` devolve 200, array com 5 ou mais caminhões e `Cache-Control` com `max-age` | `http-l7/verificar.mjs` |
| CA-03 | `GET /api/v1/eventos` devolve 200 com `text/event-stream` e `no-cache` | `http-l7/verificar.mjs` |
| CA-04 | O stream entrega ao menos 2 eventos terminados em linha em branco | `http-l7/verificar.mjs` |
| CA-05 | Os eventos trazem `retry`, `id`, `event` e `data` | `http-l7/verificar.mjs` |
| CA-06 | Rota desconhecida devolve 404 | `http-l7/verificar.mjs` |
| CA-07 | `POST` em rota de leitura devolve 405 | `http-l7/verificar.mjs` |

### Passos 4 e 5, medição e revisão

| # | Critério | Verificado por |
|---|---|---|
| CA-08 | `docs/OBSERVACOES.md` com as três medições numéricas preenchidas | Revisão |
| CA-09 | Pull Request com 2 ou mais commits semânticos e descrição em 3 seções | Revisão |
| CA-10 | Revisão da dupla vizinha com 2 ou mais comentários e 1 aprovação | Revisão |
| CA-11 | `docs/CODE_REVIEW.md` preenchido, com 2 ou mais achados contendo linha, efeito e sugestão | Revisão |
| CA-12 | Nomes de campo JSON coerentes com a Linguagem Ubíqua do SDD da dupla | Revisão |

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
| `python3 sockets-l4/verificar.py` termina sem falha? | |
| `node http-l7/verificar.mjs` termina sem falha? | |
| O `docs/CODE_REVIEW.md` tem dois achados com linha, efeito e sugestão? | |
| Vocês conseguem explicar, de boca, cada comentário que postaram? | |
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
