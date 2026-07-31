# Evidências da Aula 12

Preencha cada marcador com o que **saiu na sua máquina**, e não com o que
deveria ter saído. Valor fabricado engana a correção, não o `verificar.py`.

Formato: `MARCADOR: valor`, uma linha por marcador. O verificador procura pelo
nome do marcador e recusa a palavra `PREENCHER`.

---

## Passo 1, a SQL que os ORMs escreveram

Rode `sql/01-explorar.sql` comando a comando no `psql` e responda.

SCHEMAS_QUE_O_ORM_CRIOU: PREENCHER (quais schemas o atalho de listar schemas mostrou, além do public)

TIPO_DA_COLUNA_VALOR: PREENCHER (no que o `HasPrecision(12, 2)` do EF Core virou em `faturamento.faturas`)

INDICES_QUE_NAO_ESCREVI: PREENCHER (quantos índices existem nos dois schemas e o que cada índice único garante)

TIPO_DA_COLUNA_PESO_KG: PREENCHER (opcional: compare com o tipo de `"Valor"` e diga por que os dois diferem)

---

## Passo 2, a DDL à mão

DIMENSAO_DA_COLUNA: PREENCHER (o número dentro de `vector(...)` e de onde ele vem)

O_QUE_ACONTECE_SEM_CASCATA: PREENCHER (rode a ingestão duas vezes, com e sem `ON DELETE CASCADE`, e diga o que muda)

---

## Passo 3, a ingestão e as consultas

TRECHOS_INGERIDOS: PREENCHER (quantos trechos a ingestão criou)

SEGUNDOS_DE_INGESTAO: PREENCHER (quantos segundos ela levou, incluindo os embeddings)

BUSCA_POR_PALAVRA_CHAVE: PREENCHER (quantas linhas a busca com `ILIKE` do fim do arquivo devolveu)

---

## Passo 4, a busca por distância

MENOR_DISTANCIA: PREENCHER (a distância do primeiro resultado da sua pergunta favorita)

O_QUE_O_ILIKE_NAO_ACHOU: PREENCHER (uma pergunta cuja resposta a busca por palavra-chave não encontra e a busca por distância encontra, com o trecho recuperado)

---

## Passo 5, o índice e o plano

EXPLAIN_SEM_INDICE: PREENCHER (a linha do `Seq Scan` copiada do plano, com o Execution Time)

EXPLAIN_COM_INDICE: PREENCHER (a linha do `Index Scan using trechos_embedding_hnsw`, com o Execution Time)

TAMANHO_DO_INDICE: PREENCHER (o que a consulta 5.4 devolveu para `trechos_embedding_hnsw`)

POR_QUE_O_PLANEJADOR_ESCOLHEU_ASSIM: PREENCHER (por que o plano de 5.2 provavelmente continuou com `Seq Scan`)

---

## Passo 6, o servidor MCP

FERRAMENTAS_ANUNCIADAS: PREENCHER (o que o `tools/list` devolveu)

RECURSOS_ANUNCIADOS: PREENCHER (quantos recursos o `resources/list` devolveu)

POR_QUE_SEM_HEALTH: PREENCHER (por que este é o único serviço da plataforma sem `GET /health`)

---

## Geral

ONDE_MEDI: PREENCHER (máquina, sistema, Codespace ou local, e quanta memória)

USEI_O_RESGATE: PREENCHER (não, ou a partir de qual passo. Sem penalidade automática: é informação para a correção)
