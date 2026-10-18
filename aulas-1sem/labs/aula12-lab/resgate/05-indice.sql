-- Resgate do Passo 5: o índice HNSW completo.
--
--     cp resgate/05-indice.sql sql/05-indice.sql
--
-- A classe de operadores precisa casar com o operador usado na consulta:
-- `vector_cosine_ops` serve ao `<=>`. Criar o índice com a classe errada não
-- dá erro: ele nasce, ocupa disco e o planejador o ignora, e o plano continua
-- mostrando `Seq Scan`.

\timing on

-- Guarda o vetor de um trecho real em uma variável do psql. É isso que permite
-- o índice entrar no plano: com o vetor vindo de uma subconsulta, o planejador
-- não tem constante para procurar no grafo e cai na varredura.
SELECT embedding AS alvo FROM conhecimento.trechos ORDER BY id LIMIT 1
\gset

-- 5.1  ANTES do índice
EXPLAIN ANALYZE
SELECT id FROM conhecimento.trechos
ORDER BY embedding <=> :'alvo'::vector
LIMIT 5;

-- TODO-5 resolvido
CREATE INDEX IF NOT EXISTS trechos_embedding_hnsw
    ON conhecimento.trechos
 USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

ANALYZE conhecimento.trechos;

-- 5.2  DEPOIS do índice, com o planejador decidindo sozinho
EXPLAIN ANALYZE
SELECT id FROM conhecimento.trechos
ORDER BY embedding <=> :'alvo'::vector
LIMIT 5;

-- 5.3  DEPOIS do índice, pedindo o outro plano
SET enable_seqscan = off;

EXPLAIN ANALYZE
SELECT id FROM conhecimento.trechos
ORDER BY embedding <=> :'alvo'::vector
LIMIT 5;

RESET enable_seqscan;

-- 5.4  O custo em disco
SELECT indexrelname AS indice,
       pg_size_pretty(pg_relation_size(indexrelid)) AS tamanho
FROM pg_stat_user_indexes
WHERE schemaname = 'conhecimento'
ORDER BY indexrelname;
