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
| `resgate/docker-compose.yml`, a rede de segurança de quem travar | |

**Nada em `servicos/` é tarefa.** Não editem aqueles arquivos: o artefato de
hoje é o YAML. Se um serviço não responde, o problema está no seu
`docker-compose.yml`, não no código dele.

> Os quatro serviços das Aulas 05 e 06 que estão em `servicos/` são **versões
> mínimas**, escritas para caber no tempo desta aula. Os que vocês construíram
> de verdade também sobem aqui, e o caminho está pronto e medido em
> [Trocando pelos serviços reais das Aulas 05 e 06](#trocando-pelos-serviços-reais-das-aulas-05-e-06).
> É leitura de depois do Passo 5: fora do tempo de aula.

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

## Trocando pelos serviços reais das Aulas 05 e 06

Esta seção é **opcional** e fica fora do tempo de aula. Leia depois do Passo 5.

### Por que o kit vem com serviços mínimos

Os quatro serviços em `servicos/pedidos/`, `servicos/faturamento/`,
`servicos/frete/` e `servicos/notificacoes/` obedecem ao contrato da ADR-006
(mesmas portas, mesmas rotas, mesmo `/health`), mas são **versões mínimas**,
escritas para esta aula. Não têm o Factory Method da Aula 05, nem o Strategy e
o Decorator da Aula 06.

A razão é uma só, e é medida: **tempo de build**. Os serviços reais trazem
Maven, Spring Boot, NuGet e `npm ci`. Construir os quatro do zero, nesta
máquina, levou **1 min 56 s**, e num Codespace de dois núcleos passa disso com
folga. O laboratório tem 60 minutos e cinco passos; um build de dois a cinco
minutos antes do Passo 1 come o Passo 5 inteiro.

Os mínimos constroem em segundos e deixam a aula ser sobre o que ela é: o YAML.

### Como ligar os reais

O caminho de troca existe, está testado, e são quatro Dockerfiles multi-stage
em `docker/` mais o arquivo `compose.reais.yml`.

Ele **não** se chama `compose.reais.yml` de propósito: esse nome o
Compose leria sozinho, e quem não fizesse nada cairia nos serviços reais sem
saber, com o build longo no meio da aula. Aqui a troca é sempre explícita, com
dois `-f`, que é como se compõe arquivo de Compose no mundo real.

```bash
# 1. Diga onde estão os laboratórios anteriores, no seu .env
echo 'LOGITECH_SRC_AULA05=../aula05-lab' >> .env
echo 'LOGITECH_SRC_AULA06=../aula06-lab' >> .env

# 2. Suba compondo os dois arquivos
docker compose -f docker-compose.yml -f compose.reais.yml up -d --build

# 3. Confira qual caminho está valendo
docker compose -f docker-compose.yml -f compose.reais.yml config | grep -A2 "  pedidos:"
#    context: .../aula05-lab/pedidos    -> serviço real
docker compose config | grep -A2 "  pedidos:"
#    context: .../servicos/pedidos      -> serviço mínimo, o padrão
```

Os caminhos são relativos a este diretório, e os valores acima são o padrão:
servem para quem tem os três laboratórios lado a lado. Quem fez fork de
repositórios separados troca pelos caminhos dos seus forks, e nesse caso
precisa ajustar também o `dockerfile:` de cada serviço no `compose.reais.yml`: ele é
relativo ao `context`, e os `../` de lá contam os níveis até `docker/`.
Caminho absoluto resolve de vez quando os laboratórios não são vizinhos.

Para **voltar aos mínimos**, basta omitir o segundo `-f`:

```bash
docker compose up -d --build
```

> **Atenção, é o mesmo nome de imagem.** Os dois caminhos constroem
> `logitech-pedidos`, `logitech-faturamento`, `logitech-frete` e
> `logitech-notificacoes`. Subir com os reais sobrescreve as imagens mínimas, e
> desligar sobrescreve as reais. Por isso o `--build` nas duas direções: sem
> ele, o Compose sobe a imagem que ficou da última vez.

### Quanto custa, medido

Mesma máquina e mesma metodologia dos números da seção anterior: arm64, macOS,
Docker Desktop com 10 núcleos e 7,75 GiB para a VM.

**Build do zero**, com `--no-cache`, uma imagem por vez:

| Imagem real | Tempo | Onde o tempo vai |
|---|---|---|
| `faturamento` (.NET 8) | 8 s | `dotnet restore` 4,9 s, `dotnet publish` 1,9 s |
| `frete` (FastAPI) | 12 s | `pip install` 4,4 s |
| `pedidos` (Spring Boot) | 22 s | `mvn package` 19,5 s, com o `~/.m2` vazio |
| `notificacoes` (Node 22) | 74 s | `npm ci` 70,7 s, 58 pacotes |
| **Soma** | **1 min 56 s** | |

Com o cache do BuildKit quente, um `docker compose build` que não muda nada
volta em **1 a 2 s**. O `Dockerfile.pedidos` usa `--mount=type=cache` para o
`~/.m2`: o repositório de artefatos do Maven fica fora da imagem e sobrevive
entre builds, e é o que evita rebaixar 200 MB de Spring Boot a cada `--build`.

**Tamanho das imagens:**

| Imagem | Mínima | Real | Diferença |
|---|---|---|---|
| `logitech-frete` | 100 MB | 129 MB | +29 MB |
| `logitech-faturamento` | 166 MB | 176 MB | +10 MB |
| `logitech-notificacoes` | 229 MB | 252 MB | +23 MB |
| `logitech-pedidos` | 287 MB | 373 MB | +86 MB |
| **Soma dos quatro** | **782 MB** | **930 MB** | **+148 MB** |

**Subida e memória**, com as imagens já construídas e o volume do banco zerado.
Os números dos mínimos foram remedidos na mesma sessão, para a comparação ser
justa:

| Medida | Mínimos | Reais |
|---|---|---|
| `up -d --wait` até os oito `healthy` | 11,6 s e 11,7 s | 12,2 s e 12,3 s |
| Memória somada dos oito, em repouso | 226 MB | 388 MB |
| Maior consumidor | `pedidos`, 49 MB | `pedidos`, 158 MB |

O tempo de subida quase não muda, e isso surpreende menos do que parece: os
oito containers sobem em paralelo, e a JVM do Spring Boot leva 2,5 s para
chegar ao `Tomcat started`, dentro da janela em que os outros ainda estão
subindo. Quem paga a conta é a **memória**: +72 % no total, e a diferença mora
quase toda no `pedidos`, que sai de 49 MB para 158 MB. Os `mem_limit` do
`docker-compose.yml` continuam servindo, mas o `pedidos` passa a rodar a metade
do teto de 320 MB em vez de a um sexto dele.

### O que muda no comportamento observável

Trocar os quatro não é neutro. Estas são as diferenças que se veem de fora,
todas verificadas com a plataforma de pé:

| O que | Mínimo | Real |
|---|---|---|
| `GET /health` do `pedidos` | `{"status":"ok","servico":"pedidos","uptime_s":28,"banco":"conectado"}` | `{"status":"ok","servico":"pedidos"}` |
| `POST /api/v1/pedidos`, entrada | `{cliente, origem, destino, pesoKg, modalidade}` | `{cliente, tipoCliente, origem, destino, enderecoEntrega, pesoKg, valor}` |
| `POST /api/v1/pedidos`, saída | tem o campo `jornada` com as quatro etapas | `{id, cliente, tipoCliente, ..., status, numeroNotaFiscal}`, sem `jornada` |
| `POST /api/v1/frete/cotacao`, origem e destino | cidade ou CEP, `"Guarulhos-SP"` | só o código de três letras do CD, `"GRU"` |
| `POST /api/v1/frete/cotacao`, modalidades | `economico`, `expresso`, `refrigerado` | `economico`, `expresso`, `padrao` |
| Schema `pedidos` no PostgreSQL | criado pelo próprio serviço, na subida | precisa ser criado de fora |
| Serviços declarados | 8 | 9, com o `prepara-schemas` |

As três primeiras linhas são a mesma decisão vista de ângulos diferentes: o
serviço mínimo foi escrito para **esta** aula e devolve o que esta aula quer
provar (o banco conectado, a jornada percorrendo a plataforma); o real foi
escrito para a Aula 05 e devolve o contrato da ADR-006, nada além.

A quinta linha é a que dá mais trabalho. O `pedidos` real usa
`hibernate.default_schema=pedidos` com `ddl-auto=update`: o Hibernate cria as
**tabelas**, mas não cria o **schema** que as abriga. Na Aula 05 o schema
nasceu de um `psql -c "CREATE SCHEMA IF NOT EXISTS pedidos"` rodado à mão. O
`compose.reais.yml` traduz aquele comando para YAML, no serviço efêmero `prepara-schemas`,
que roda antes do `pedidos` e morre. É a única peça que a troca acrescenta,
e ela existe porque a regra deste laboratório é não tocar no código das aulas
anteriores.

Sem ela o sintoma é o pior possível: o container fica `healthy` e o serviço não
funciona, com `ERROR: schema "pedidos" does not exist` enterrado no log.

### O que o `verificar.py` passa a acusar

O verificador foi escrito para o caminho padrão. Com os reais no lugar, **os
critérios 1 e 5 reprovam**, e reprovam por motivo legítimo:

- **Critério 1** exige `banco: "conectado"` no `/health` do `pedidos`. O
  serviço real não expõe esse campo.
- **Critério 5** exige exatamente os oito serviços da ADR-006 e um
  `POST /api/v1/pedidos` devolvendo `jornada` com quatro etapas em `ok`. Com o
  caminho dos reais há nove serviços, e o real não devolve `jornada`.

Os critérios 2, 3 e 4 continuam válidos: o DNS interno, a dívida da ADR-002 e o
AI Gateway não dependem de qual das duas versões está no ar.

**Entregue o laboratório pelo caminho padrão.** A troca é para depois, e o que
ela prova está no parágrafo seguinte.

### O que a troca prova

Com os reais no lugar, a plataforma sobe inteira e um pedido atravessa dois
serviços em duas linguagens diferentes:

```bash
curl -s --connect-timeout 5 --max-time 20 -X POST http://localhost:8080/api/v1/pedidos \
  -H 'content-type: application/json' \
  -d '{"cliente":"ana@logitech.com.br","tipoCliente":"PADRAO","origem":"GRU",
       "destino":"CNF","enderecoEntrega":"Av. Amazonas 1000, Betim-MG",
       "pesoKg":820,"valor":15400.00}'
# {"id":"5e047ac2-...","status":"FATURADO","numeroNotaFiscal":"NF-000001", ...}

curl -s --connect-timeout 5 --max-time 15 http://localhost:5080/api/v1/faturas
# [{"pedidoId":"5e047ac2-...","numeroNotaFiscal":"NF-000001","meioPagamento":"BOLETO", ...}]
```

O Java gravou no schema `pedidos`, chamou o C# pelo nome `faturamento` na rede
interna, o C# gravou no schema `faturamento` e devolveu a nota fiscal. É a
promessa do módulo inteiro em duas chamadas.

Duas advertências:

- `tipoCliente` só aceita `PADRAO` e `OURO`. Qualquer outro valor devolve
  `400`, porque é o `ConectorFaturamento` da Aula 05 que decide.
- Se o **TODO-2 da Aula 05** ainda estiver em aberto no seu fork, o
  `POST /api/v1/pedidos` devolve `400` com a mensagem da fábrica não
  implementada. A troca só entrega a jornada completa depois que aquele
  laboratório estiver fechado, e isso é proposital: é a espiral cobrando o que
  ficou para trás.

### Os quatro Dockerfiles

Ficam em `docker/`, um por serviço, e seguem as mesmas regras que a **Aula 03**
cobrou: dois estágios nomeados, base alpine no estágio final, usuário não-root
com UID acima de 10000, nunca `COPY . .`, `EXPOSE` com a porta do contrato.
Vale abrir os quatro: cada um resolve o mesmo problema numa stack diferente.

| Arquivo | Estágio de build | Estágio final | Usuário |
|---|---|---|---|
| `Dockerfile.pedidos` | `maven:3.9-eclipse-temurin-21` | `eclipse-temurin:21-jre-alpine` | `logitech`, UID 10001 |
| `Dockerfile.faturamento` | `mcr.microsoft.com/dotnet/sdk:8.0-alpine` | `mcr.microsoft.com/dotnet/aspnet:8.0-alpine` | `logitech`, UID 10002 |
| `Dockerfile.frete` | `python:3.12-alpine` | `python:3.12-alpine` | `logitech`, UID 10003 |
| `Dockerfile.notificacoes` | `node:22-alpine` | `node:22-alpine` | `logitech`, UID 10004 |

Quatro decisões que só ficam claras lendo o arquivo, e que valem como conteúdo:

- **`pedidos`**: o estágio de build **não** é alpine, e é de propósito. A regra
  pede base enxuta no estágio final, que é o que vai para o registro; o estágio
  de compilação é descartado e pode ser gordo.
- **`faturamento`**: `tests/` e `Faturamento.sln` ficam de fora do `COPY`, e é
  por isso que o `restore` e o `publish` apontam para o `.csproj` direto. A
  solução referencia o projeto de teste, e teste não entra em imagem.
- **`frete`**: a base **precisa** ser alpine. O `healthcheck` que vocês
  escreveram usa `wget`, que vem no BusyBox do alpine e não existe em
  `python:3.12-slim`. Trocar a base deixa o serviço respondendo e o container
  eternamente `unhealthy`.
- **`notificacoes`**: o `tsx` sobrevive ao estágio final, contrariando a regra
  de não levar ferramenta de desenvolvimento. Não é descuido: `src/servidor.ts`
  importa `./adaptador` sem extensão, o apagador de tipos nativo do Node 22 não
  reescreve caminho de importação, e o servidor só escuta se `process.argv[1]`
  terminar em `servidor.ts`. Compilar para `.js` deixaria o container `Up` para
  sempre, sem nunca aceitar conexão.

### Se o build do `pedidos` falhar por rede

Sintoma inconfundível: dezenas de
`Connect to repo.maven.apache.org:443 failed: Connection refused` em menos de
dois segundos, com a mesma máquina baixando o mesmo arquivo por `wget` sem
reclamar. O Maven baixa artefatos em cinco conexões simultâneas, e há VPN,
proxy e antivírus que recusam a segunda conexão simultânea para o mesmo
destino. O `Dockerfile.pedidos` deixa a válvula pronta:

```bash
docker compose build --build-arg MAVEN_THREADS_ARTEFATO=1 pedidos
```

O build fica mais lento e passa. Foi assim que os números desta seção foram
medidos.

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

## O diretório `resgate/`

Atividade em passos tem um risco que uma atividade única não tem: travar no
Passo 2 mata os Passos 3, 4 e 5. `resgate/docker-compose.yml` é o arquivo
completo, comentado, pronto para copiar:

```bash
cp resgate/docker-compose.yml docker-compose.yml
docker compose up -d --build
```

Quem usar registra `USEI_O_RESGATE` em `docs/EVIDENCIAS.md`, dizendo a
partir de qual passo. Sem penalidade automática: é informação para a
correção, não armadilha.

---

## Onde isso vai dar

Na **Aula 08** o agente de atendimento chama `PATCH /api/v1/pedidos/{id}/endereco`
e `GET /api/v1/pedidos/{id}/status` por Function Calling, e usa este mesmo AI
Gateway como backend de modelo. O `docker-compose.yml` que vocês escreveram
hoje é o ambiente onde aquele agente roda. Guardem o fork.
