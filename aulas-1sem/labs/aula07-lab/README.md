# Laboratório Prático - Aula 07

## Disciplina: Microservice and Web Engineering & IT Services
**Prof.º José Romualdo | FIAP Sistemas de Informação**

### Case: LogiTech Enterprise AI Platform (Fase 7, Orquestração)

Na Aula 03 vocês empacotaram dois serviços em imagens Docker e os subiram um a
um, à mão. Nas Aulas 05 e 06 a plataforma ganhou mais quatro: Pedidos em Java,
Faturamento em C#, Frete em Python e Notificações em Node. Some o PostgreSQL e
o resultado é **sete serviços que ninguém sobe duas vezes do mesmo jeito**.

Hoje esses comandos viram um arquivo. Um `docker compose up -d` põe a
plataforma inteira de pé, na ordem certa, com rede, variáveis, volumes e
limites de memória. E a plataforma ganha o oitavo serviço, o **AI Gateway**:
o ponto único por onde toda chamada de IA passa, com Facade escondendo os
provedores, Strategy escolhendo entre eles, fallback de verdade, limite de
taxa e cache.

**Atividade em grupo**, cinco passos. Cada passo sobe o que você acabou de
escrever.

---

## O que já vem pronto, e o que vocês fazem

| Vem pronto, é modelo | Vocês escrevem |
|---|---|
| `servicos/pedidos/`, `servicos/faturamento/`, `servicos/frete/`, `servicos/notificacoes/`, congelados das Aulas 05 e 06 | O `docker-compose.yml` da raiz, preenchendo `TODO-1` a `TODO-5` |
| `servicos/coletor/` e `servicos/painel/`, congelados das Aulas 02 e 03, **evoluídos** para pagar a dívida da ADR-002 | `docs/EVIDENCIAS.md` com os 12 marcadores |
| `servicos/ai-gateway/`, o conteúdo novo da aula, com Facade, Strategy, fallback, cache e métricas | O `.env` a partir do `.env.exemplo` |
| Um `Dockerfile` multi-stage por serviço, com `USER` não-root | Os commits, um por passo |
| `verificar.py`, a autoavaliação dos cinco critérios | |
| `gabarito/docker-compose.yml`, a rede de segurança de quem travar | |

**Nada em `servicos/` é tarefa.** Não editem aqueles arquivos: o artefato de
hoje é o YAML. Se um serviço não responde, o problema está no seu
`docker-compose.yml`, não no código dele.

---

## Pré-requisitos

- Fork do repositório `josercf/mwe-2026-2-lab07-compose-gateway` (nunca clone
  direto).
- GitHub Codespaces, ou Docker Desktop local com pelo menos 4 GB livres para a
  VM do Docker.
- A rede e o volume herdados da Aula 03. Se você fez a Aula 03 nesta máquina,
  os dois já existem; se não, crie agora, com os mesmos comandos de lá:

```bash
docker network create logitech-net
docker volume  create logitech-telemetria
```

> **Pare o Ollama antes do primeiro `docker compose up`.**
>
> ```bash
> pkill ollama
> ```
>
> São oito containers, e no Codespace de dois núcleos o modelo local disputa
> memória e CPU com todos eles. O AI Gateway continua subindo e continua
> saudável sem o Ollama: ele responde `/health` normalmente e o provedor
> remoto, sem credencial, falha como esperado. O que não acontece nesse
> cenário é o provedor **local** responder, e aí `POST /v1/chat/completions`
> devolve `503` com o motivo de cada provedor no corpo.
>
> O **Passo 4** manda religar o Ollama (`ollama serve &`) por dois minutos,
> só para colher a evidência do fallback e do cache, e pará-lo de novo antes
> de medir a memória no Passo 5.

> **Se a sua Aula 05 ainda estiver de pé nesta máquina**, pare o PostgreSQL
> que você subiu por `docker run` lá:
>
> ```bash
> docker rm -f logitech-postgres
> ```
>
> Ele ocupa a porta 5432 e, se estiver na `logitech-net`, disputa o nome
> `postgres` com o serviço do Compose. Rede compartilhada entre laboratórios
> é conveniência, não isolamento.

---

## Como abrir o Codespace

1. Fork de `josercf/mwe-2026-2-lab07-compose-gateway` para a sua conta.
2. No fork, **Code > Codespaces > Create codespace on main**.
3. Aguarde o `post-create.sh` terminar.
4. Prepare o ambiente:

```bash
cp .env.exemplo .env
docker network create logitech-net       # se ainda não existir
docker volume  create logitech-telemetria
pkill ollama
```

---

## A plataforma que vocês vão orquestrar

Os oito serviços, com nome, porta e origem. Isto é o **contrato da
plataforma** (ADR-006): trocar um nome ou uma porta aqui quebra a Aula 08.

| Serviço | Linguagem | Porta | Nasce na | Rotas que outros consomem |
|---|---|---|---|---|
| `postgres` | PostgreSQL 16 | 5432, não publicada | Aula 07 | - |
| `pedidos` | Java 21 | 8080 | Aula 05 | `/health`, `/api/v1/pedidos`, `.../{id}/status`, `.../{id}/endereco` |
| `faturamento` | C#, .NET 8 | 5080 | Aula 05 | `/health`, `/api/v1/faturas` |
| `frete` | Python, FastAPI | 8000 | Aula 06 | `/health`, `/api/v1/frete/cotacao` |
| `notificacoes` | Node 22, TypeScript | 3001 | Aula 06 | `/health`, `/api/v1/notificacoes` |
| `coletor` | Python | 8081/udp e **8082/tcp** | Aula 02 | `/health`, **`/telemetria`** |
| `painel` | Node | 3000 | Aula 02 | `/health`, `/`, `/api/v1/posicoes`, `/api/v1/eventos` |
| `ai-gateway` | Python, FastAPI | 4000 | **Aula 07** | `/health`, `/v1/chat/completions`, `/v1/metricas` |

A porta **8082 do coletor é nova**, e existe para pagar a dívida da ADR-002.

---

## Os cinco passos

Cada passo tem a instrução completa em comentário, dentro do próprio
`docker-compose.yml`. Esta seção é o resumo.

### Passo 1, o banco e quem depende dele (`TODO-1a`, `TODO-1b`)

**Não pule a primeira metade.** Suba a plataforma como ela vem, com o
`postgres` **sem** `healthcheck` e o `pedidos` com `depends_on` na forma de
lista:

```bash
docker compose up -d --build
docker compose ps -a
docker compose logs pedidos
```

O `pedidos` vai estar `Exited (1)`. Copie a mensagem para
`PEDIDOS_SEM_HEALTHCHECK` em `docs/EVIDENCIAS.md`. É a Pergunta de
Verificação 1 provada na sua máquina, não afirmada em slide.

Só então preencha o `healthcheck` do `postgres` (`TODO-1a`) e troque o
`depends_on` pela forma com `condition: service_healthy` (`TODO-1b`).

### Passo 2, os três serviços das Aulas 05 e 06 (`TODO-2`)

Declare `faturamento`, `frete` e `notificacoes` com porta, rede, variáveis e
**limite de memória**. Prove o DNS interno:

```bash
docker compose exec pedidos wget -qO- http://frete:8000/health
```

`frete` é um nome que só existe dentro da rede da plataforma. Registre a
resposta em `DNS_INTERNO`.

### Passo 3, a dívida da ADR-002 (`TODO-3`)

Declare `coletor` e `painel`. O painel deixa de ler o arquivo compartilhado e
passa a consumir `GET /telemetria` na 8082 do coletor, por
`LOGITECH_TELEMETRIA_URL`.

**O `painel` não monta volume nenhum.** Se você montou
`logitech-telemetria` nele, a dívida não foi paga: ele só trocou de endereço.

```bash
curl -s localhost:3000/health          # o campo "fonte" precisa dizer "http"
```

Mande telemetria de verdade e veja chegar no painel:

```bash
python3 - <<'PY'
import socket, json
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
for i, placa in enumerate(["LGT-1A23", "LGT-4B56", "LGT-7C89"]):
    s.sendto(json.dumps({"placa": placa, "lat": -23.5 - i*0.4,
                         "lng": -46.6 - i*0.3, "velocidade_kmh": 80 + i}).encode(),
             ("127.0.0.1", 8081))
print("3 posições enviadas")
PY
curl -s localhost:8082/telemetria
curl -s localhost:3000/api/v1/posicoes
```

### Passo 4, o AI Gateway (`TODO-4`)

Religue o Ollama e declare o `ai-gateway`, com os dois provedores e o
`extra_hosts` que permite alcançar o Ollama do host.

Faça a **mesma pergunta três vezes** e leia as métricas:

```bash
ollama serve &
for i in 1 2 3; do
  curl -s localhost:4000/v1/chat/completions \
    -H 'Content-Type: application/json' -H 'X-Servico: painel' \
    -d '{"messages":[{"role":"user","content":"Responda em uma frase curta: o que faz uma transportadora de cargas?"}]}'
  echo
done
curl -s localhost:4000/v1/metricas
docker compose logs ai-gateway | grep FALLBACK
```

A primeira chamada demora: ela vai ao modelo. A segunda e a terceira voltam
do cache em milissegundos. Registre `FALLBACK_ACIONADO` e `ACERTOS_DE_CACHE`.

Depois, pare o Ollama de novo (`pkill ollama`) antes do Passo 5.

### Passo 5, os oito de pé e saudáveis (`TODO-5a`, `TODO-5b`)

`docker compose ps` mostra `Up` para todo container que subiu, e `healthy`
só para os que declaram `healthcheck`. Acrescente o dos oito e meça:

```bash
docker compose down
time docker compose up -d --wait
docker compose ps
docker stats --no-stream --format '{{.Name}} {{.MemUsage}}'
```

Depois, um pedido percorrendo a plataforma inteira:

```bash
curl -s -X POST localhost:8080/api/v1/pedidos \
  -H 'Content-Type: application/json' \
  -d '{"cliente":"ana@logitech.com.br","origem":"Guarulhos-SP",
       "destino":"Betim-MG","pesoKg":820,"modalidade":"expresso"}'
```

O campo `jornada` precisa trazer `ok` nas quatro etapas: `frete`, `pedidos`,
`faturamento` e `notificacoes`.

---

## Ordem de corte

Se o tempo apertar, corte de baixo para cima. Os passos 1, 2 e 3 são o
mínimo entregável; o 4 é o conteúdo autoral da aula; o 5 fecha.

| Prioridade | O que |
|---|---|
| 1 | Passos 1, 2 e 3, com os critérios 1 a 3 verdes |
| 2 | Passo 4 |
| 3 | Passo 5 |
| Cortável | O ajuste fino dos limites de memória (deixe os valores sugeridos) |

---

## Valores de referência, medidos

Como na Aula 03, os números abaixo foram **medidos**, não estimados, na
validação deste laboratório. Servem de ordem de grandeza: os seus vão
diferir, e é isso que `ONDE_MEDI` registra.

Medidos em **arm64, macOS, Docker Desktop com 10 núcleos e 7,75 GiB para a
VM**, com as imagens já construídas e o volume do banco zerado:

| Medida | Valor |
|---|---|
| Tempo do `up -d --wait` até os oito `healthy` | **11,9 s** |
| Memória somada dos oito containers, em repouso | **228 MB** |
| Maior consumidor | `pedidos` (JVM), **46 MB** |
| Teto declarado no `docker-compose.yml` | 1632 MB |
| Menor consumidor | `painel`, 9,7 MB |
| Primeira resposta do AI Gateway pelo provedor local | 152,7 s (modelo frio) |
| Segunda e terceira, servidas pelo cache | 5 ms e 0 ms |
| Serviços que ficaram `unhealthy` com `localhost` no healthcheck | 4 de 8 |

O contraste da penúltima linha é o argumento inteiro do cache em um número:
**152.660 ms contra 0 ms** para a mesma pergunta.

A última linha é uma armadilha medida, não teórica. Com o healthcheck escrito
como `http://localhost:PORTA/health`, **quatro dos oito** serviços ficaram
`unhealthy` mesmo respondendo: dentro de uma imagem Alpine o `localhost` pode
resolver primeiro para `::1`, em IPv6, enquanto o servidor escuta em IPv4. Por
isso todos os healthchecks deste laboratório usam o literal `127.0.0.1`.

Tamanho das imagens construídas:

| Imagem | Tamanho |
|---|---|
| `logitech-coletor` | 78,9 MB |
| `logitech-frete` | 100 MB |
| `logitech-ai-gateway` | 103 MB |
| `logitech-faturamento` | 166 MB |
| `logitech-notificacoes` | 229 MB |
| `logitech-painel` | 229 MB |
| `logitech-pedidos` | 287 MB |

---

## Critérios de aceitação

A tabela abaixo espelha, passo por passo, o que `verificar.py` confere.

| # | Critério | Verificado por |
|---|---|---|
| CA-01 | `postgres` com `healthcheck` usando `pg_isready`; `pedidos` com `depends_on.postgres.condition: service_healthy`; `PEDIDOS_SEM_HEALTHCHECK` preenchido; `/health` do `pedidos` respondendo com o banco conectado | `verificar.py --criterio 1` |
| CA-02 | `faturamento`, `frete` e `notificacoes` declarados, cada um com a porta do contrato, na rede `logitech-net` e com limite de memória; os três respondendo em `/health`; `DNS_INTERNO` preenchido e confirmado por uma chamada real de container para container | `verificar.py --criterio 2` |
| CA-03 | `coletor` publicando 8081/udp e 8082/tcp e montando `logitech-telemetria`; `painel` com `LOGITECH_TELEMETRIA_URL` apontando para `coletor:8082` e **sem volume nenhum**; `GET /telemetria` respondendo; `/health` do painel dizendo `fonte: http`; `PAINEL_LE_ARQUIVO: não` | `verificar.py --criterio 3` |
| CA-04 | `ai-gateway` na porta 4000 com `extra_hosts`; `GET /v1/metricas` com `fallback.acionado` >= 1 e `cache.acertos` >= 2; `FALLBACK_ACIONADO` com o trecho de log e `ACERTOS_DE_CACHE` >= 2 | `verificar.py --criterio 4` |
| CA-05 | Os 8 serviços do contrato declarados, nem um a mais nem um a menos, todos com `healthcheck`; `docker compose ps` com os 8 `healthy`; `TEMPO_ATE_TODOS_SAUDAVEIS_S` e `MEMORIA_TOTAL_MB` preenchidos; um `POST /api/v1/pedidos` com as quatro etapas da jornada em `ok` | `verificar.py --criterio 5` |

Rode a suíte inteira, ou um critério isolado, a qualquer momento:

```bash
python3 verificar.py               # roda os cinco critérios
python3 verificar.py --criterio 3  # roda só um
```

O verificador **checa o `/health` dos sete serviços HTTP antes de julgar o
YAML**, e imprime o resultado. Um critério que falha porque o container nem
subiu tem conserto diferente de um critério que falha porque falta uma linha
no arquivo, e misturar os dois manda você procurar no lugar errado.

### O que a máquina prova, e o que fica por sua conta

| Passo | Verificado por máquina | Declarado por você |
|---|---|---|
| 1 | O `healthcheck` do `postgres` usa `pg_isready`; o `depends_on` do `pedidos` tem `condition: service_healthy`; o `pedidos` responde `/health` com `banco: conectado` | `PEDIDOS_SEM_HEALTHCHECK`: o verificador confere que há texto preenchido, não que ele veio de uma execução real, porque o container que falhou já foi recriado quando ele roda. `SEGUNDOS_ATE_O_PRIMEIRO_HEALTHY` idem |
| 2 | Os três serviços existem, com a porta do contrato, na rede certa e com limite de memória; os três respondem `/health`; um `docker compose exec` real prova o DNS interno | Nada relevante |
| 3 | O `painel` não monta volume, tem a variável certa, e o `/health` dele informa `fonte: http`; o `coletor` publica as duas portas e monta o volume; `GET /telemetria` responde o contrato | `PAINEL_LE_ARQUIVO`: precisa dizer "não", mas quem prova isso são as checagens de máquina acima, não o texto |
| 4 | `fallback.acionado` e `cache.acertos` lidos ao vivo de `GET /v1/metricas`, no gateway rodando | `FALLBACK_ACIONADO`: o verificador confere que o trecho parece um log de fallback, não que você o copiou do seu próprio container |
| 5 | Os oito serviços declarados e com `healthcheck`; `docker compose ps` com os oito `healthy`; um `POST /api/v1/pedidos` de verdade, com as quatro etapas da jornada | `TEMPO_ATE_TODOS_SAUDAVEIS_S`, `MEMORIA_TOTAL_MB` e `MEMORIA_MAIOR_CONSUMIDOR_MB`: o verificador confere que são números positivos, mas não cronometra nem mede sozinho. `ONDE_MEDI` é texto livre |

Nas linhas onde a máquina não prova tudo, o professor confere na correção.
Preencher com valor fabricado engana a correção, não o `verificar.py`.

---

## O verificador tem testes

```bash
python3 -m unittest discover -v
```

29 testes cobrem as funções puras de `verificar.py`: leitura de marcador,
conversão de número decimal em português, normalização do `environment`,
leitura de limite de memória nas duas grafias, de portas nas duas formas e
de volumes. Nenhum deles precisa de Docker rodando.

---

## Como entregar

**Um commit por passo concluído**, no padrão Conventional Commits:

```bash
git add docker-compose.yml docs/EVIDENCIAS.md
git commit -m "feat(passo-1): healthcheck do banco e depends_on com condição"

git add docker-compose.yml
git commit -m "feat(passo-2): faturamento, frete e notificações orquestrados"

git add docker-compose.yml docs/EVIDENCIAS.md
git commit -m "feat(passo-3): painel consumindo a API do coletor (ADR-002)"

git add docker-compose.yml docs/EVIDENCIAS.md
git commit -m "feat(passo-4): AI Gateway com fallback e cache"

git add docker-compose.yml docs/EVIDENCIAS.md
git commit -m "feat(passo-5): os oito serviços saudáveis"

git push
```

A progressão precisa ficar visível no histórico do seu fork: cinco commits,
não um único commit final com tudo dentro.

Ao terminar, submeta a **URL do seu fork** no formulário da aula.

> **Formulário:** a URL será publicada pelo professor antes da aula.

Um envio por grupo, até o fim da aula.

---

## O diretório `gabarito/`

Atividade em passos tem um risco que uma atividade única não tem: travar no
Passo 2 mata os Passos 3, 4 e 5. `gabarito/docker-compose.yml` é o arquivo
completo, comentado, pronto para copiar:

```bash
cp gabarito/docker-compose.yml docker-compose.yml
docker compose up -d --build
```

Quem usar registra `USEI_O_GABARITO` em `docs/EVIDENCIAS.md`, dizendo a
partir de qual passo. Sem penalidade automática: é informação para a
correção, não armadilha.

---

## Onde isso vai dar

Na **Aula 08** o agente de atendimento chama `PATCH /api/v1/pedidos/{id}/endereco`
e `GET /api/v1/pedidos/{id}/status` por Function Calling, e usa este mesmo AI
Gateway como backend de modelo. O `docker-compose.yml` que vocês escreveram
hoje é o ambiente onde aquele agente roda. Guardem o fork.
