# Evidências, Aula 07, Docker Compose e AI Gateway

Formulário único, preenchido à medida que você fecha cada passo.
`verificar.py` lê estes marcadores procurando `MARCADOR: valor`. Não apague o
nome do marcador, não mude a grafia, e troque `PREENCHER` pelo valor real
medido na sua máquina. Um `PREENCHER` esquecido reprova o critério
correspondente.

Cinco dos campos abaixo são valores numéricos ou medidas:
`TEMPO_ATE_TODOS_SAUDAVEIS_S`, `MEMORIA_TOTAL_MB`, `ACERTOS_DE_CACHE`,
`MEMORIA_MAIOR_CONSUMIDOR_MB` e `SEGUNDOS_ATE_O_PRIMEIRO_HEALTHY`. Os demais
são prova de execução.

---

## Passo 1, o banco e quem depende dele

Antes de preencher o `TODO-1a`, suba a plataforma como ela vem no esqueleto
(postgres **sem** `healthcheck`, `pedidos` com `depends_on` em lista) e leia:

```bash
docker compose up -d --build
docker compose logs pedidos
```

Cole abaixo, em uma linha, a mensagem de erro que o `pedidos` imprimiu ao
morrer. É a resposta da Pergunta de Verificação 1 provada na sua máquina, não
afirmada em slide.

```
PEDIDOS_SEM_HEALTHCHECK: PREENCHER
```

Depois de preencher os `TODO-1a` e `TODO-1b`, meça quanto tempo o
`postgres` levou do `up` até ficar `healthy`. O comando abaixo imprime o
número em segundos:

```bash
docker inspect --format '{{.State.Health.Status}}' $(docker compose ps -q postgres)
```

O `docker compose ps -q postgres` devolve o id do container do serviço, sem
depender do nome: nenhum serviço deste laboratório declara `container_name`.

```
SEGUNDOS_ATE_O_PRIMEIRO_HEALTHY: PREENCHER
```

---

## Passo 2, os três serviços das Aulas 05 e 06

Prove que o DNS interno da rede `logitech-net` funciona: um container
chamando outro **pelo nome do serviço**, sem endereço IP e sem passar pelo
host.

```bash
docker compose exec pedidos wget -qO- http://frete:8000/health
```

Cole a resposta em uma linha:

```
DNS_INTERNO: PREENCHER
```

---

## Passo 3, a dívida da ADR-002

Até a Aula 03 o painel lia o arquivo que o coletor gravava. Depois do Passo 3
ele consulta `GET /telemetria` na porta 8082. Confirme:

```bash
curl -s localhost:3000/health | grep -o '"fonte":"[^"]*"'
docker compose config | grep -A5 'painel:' | grep volumes
```

O primeiro comando precisa dizer `http`. O segundo não pode devolver nada.

```
PAINEL_LE_ARQUIVO: PREENCHER
```

Escreva `não` quando as duas condições estiverem cumpridas.

---

## Passo 4, o AI Gateway

Religue o Ollama (`ollama serve &`) e faça a **mesma pergunta três vezes**:

```bash
for i in 1 2 3; do
  curl -s localhost:4000/v1/chat/completions \
    -H 'Content-Type: application/json' \
    -H 'X-Servico: painel' \
    -d '{"messages":[{"role":"user","content":"Em uma frase, o que faz uma transportadora?"}]}' \
    | head -c 200
  echo
done
curl -s localhost:4000/v1/metricas
```

Cole o trecho de `docker compose logs ai-gateway` que mostra o gateway
caindo do provedor remoto para o local. Ele começa com `[FALLBACK]`:

```
FALLBACK_ACIONADO: PREENCHER
```

E o número de acertos de cache lido em `GET /v1/metricas`, no campo
`cache.acertos`. Precisa ser no mínimo 2:

```
ACERTOS_DE_CACHE: PREENCHER
```

---

## Passo 5, os oito de pé

Com tudo saudável, meça. O tempo é do `docker compose up -d` até o
`docker compose ps` mostrar os oito `healthy`:

```bash
time (docker compose up -d --wait)
docker stats --no-stream --format '{{.Name}} {{.MemUsage}}'
```

```
TEMPO_ATE_TODOS_SAUDAVEIS_S: PREENCHER
MEMORIA_TOTAL_MB: PREENCHER
MEMORIA_MAIOR_CONSUMIDOR_MB: PREENCHER
QUAL_O_MAIOR_CONSUMIDOR: PREENCHER
```

E a arquitetura em que você mediu (`uname -m` e onde rodou), porque o número
sozinho não diz nada:

```
ONDE_MEDI: PREENCHER
```

---

## Uso do gabarito

Preencha em qualquer momento em que tiver copiado `gabarito/docker-compose.yml`
para a raiz do laboratório, em vez de escrever o seu. Usar o gabarito não
reprova nenhum critério que o `verificar.py` consiga confirmar por máquina,
mas é informação que o professor precisa ter na correção.

```
USEI_O_GABARITO: PREENCHER
```

Se você não usou o gabarito em passo nenhum, escreva `USEI_O_GABARITO: não`.
