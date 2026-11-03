# Evidências da Aula 16 - integração end-to-end e simulado da banca

Preencha cada marcador com o que **aconteceu na sua máquina**. Número medido
vale mais do que número esperado, e número copiado de outro grupo não vale
nada: a banca pergunta pela máquina de vocês.

O `verificar.py` lê estes marcadores. `PREENCHER` conta como vazio.

---

## Frente 1 - a plataforma de pé

MAQUINA: PREENCHER (modelo, memória total e núcleos. Ex.: MacBook Pro M4, 16 GB, 10 núcleos, Docker Desktop com 8 GB)

TEMPO_ATE_TODOS_SAUDAVEIS_S: PREENCHER (segundos do `up -d --wait` até os treze `healthy`)

MEMORIA_TOTAL_MB: PREENCHER (soma do `docker stats --no-stream`, em repouso)

SERVICOS_SAUDAVEIS: PREENCHER (quantos de 13)

Se os treze **não** couberem na sua máquina, escreva isso aqui com os números
que você observou, e diga por quais grupos você subiu. Isso é informação, não
fracasso, e a banca prefere ouvir a medição a ouvir que "deu certo".

SUBI_POR_GRUPOS: PREENCHER (não / sim, e quais grupos)

### As seis falhas plantadas

Uma linha por falha: qual era o sintoma, como você descobriu, e o que mudou.

FALHA_1_IPV6: PREENCHER
FALHA_2_ISSUER: PREENCHER
FALHA_3_PORTA: PREENCHER
FALHA_4_DEPENDS_ON: PREENCHER
FALHA_5_STDIN: PREENCHER
FALHA_6_AUTH: PREENCHER

USEI_O_RESGATE: PREENCHER (não / sim, e em qual falha)

---

## Frente 2 - fluxo autenticado ponta a ponta

TOKEN_EXPIRA_EM_S: PREENCHER (`exp - iat` do token, lido do próprio token)

PAPEIS_NO_TOKEN: PREENCHER (copiado de `realm_access.roles`)

ISS_DO_TOKEN: PREENCHER

MATRIZ_401_403: PREENCHER (uma linha por chamada: rota, papel e status)

JORNADA_ADMIN: PREENCHER (o campo `jornada` da resposta do POST como carla.admin)

JORNADA_CLIENTE: PREENCHER (o mesmo POST como ana.cliente. Explique em uma frase por que ele difere)

NUMERO_DA_FATURA: PREENCHER

---

## Frente 3 - guardrail e injeção

INJECAO_ANTES: PREENCHER (com `LOGITECH_GUARDRAILS_ATIVOS=false`, o que o modelo respondeu)

INJECAO_RECUSADA: PREENCHER (o corpo do 422, com `regra` e `motivo`)

GUARDRAIL_RECUSAS_ENTRADA: PREENCHER (o contador de `GET /v1/metricas`)

FORMULACAO_QUE_PASSOU: PREENCHER (uma formulação SUA que furou o filtro. Se
nenhuma passou, escreva quantas você tentou. Filtro que ninguém tentou furar
não é defesa.)

MASCARAMENTO: PREENCHER (a saída mascarada de um CPF, de um cartão e de uma placa)

---

## Frente 4 - RAG e MCP

RAG_FONTE_CITADA: PREENCHER (contrato, cliente e distância do trecho no topo)

RAG_RESPONDE_A_PERGUNTA: PREENCHER (sim/não, e por quê)

MCP_FERRAMENTAS: PREENCHER (a lista que `tools/list` devolveu)

MCP_RECURSOS: PREENCHER (quantos contratos o `resources/list` anunciou)

---

## Frente 5 - cadeia de suprimentos

DATA_DA_VARREDURA: PREENCHER (resultado de Trivy sem data não se confere depois)

VERSAO_DO_TRIVY: PREENCHER

CVES_CRITICAL_ANTES: PREENCHER

CVES_CRITICAL_DEPOIS: PREENCHER (precisa ser 0)

CVES_HIGH_ACEITAS: PREENCHER (e cada uma justificada em docs/EXCECOES.md)

---

## A banca

ROTEIRO_ESCRITO: PREENCHER (sim/não. O roteiro fica em docs/ROTEIRO-BANCA.md)

ENSAIO_CRONOMETRADO_S: PREENCHER (quantos segundos durou o ensaio completo)

O_QUE_QUEBROU_NO_ENSAIO: PREENCHER
