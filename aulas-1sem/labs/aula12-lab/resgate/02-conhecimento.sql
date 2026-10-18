-- Resgate do Passo 2: a DDL completa do schema `conhecimento`.
--
--     cp resgate/02-conhecimento.sql sql/02-conhecimento.sql
--
-- Quem usar registra USEI_O_RESGATE em docs/EVIDENCIAS.md, dizendo a partir de
-- qual passo. Sem penalidade automática: é informação para a correção.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA IF NOT EXISTS conhecimento;

CREATE TABLE IF NOT EXISTS conhecimento.contratos (
    id        bigserial    PRIMARY KEY,
    cliente   varchar(160) NOT NULL,
    titulo    varchar(200) NOT NULL,
    vigencia  varchar(60)  NOT NULL,
    arquivo   varchar(200) NOT NULL UNIQUE,
    criado_em timestamptz  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS conhecimento.trechos (
    id          bigserial PRIMARY KEY,
    contrato_id bigint    NOT NULL
                REFERENCES conhecimento.contratos (id) ON DELETE CASCADE,
    ordem       int       NOT NULL,
    texto       text      NOT NULL,
    embedding   vector(768),
    CONSTRAINT trechos_ordem_unica_por_contrato UNIQUE (contrato_id, ordem)
);

SELECT c.relname AS tabela, a.attname AS coluna,
       format_type(a.atttypid, a.atttypmod) AS tipo
FROM pg_attribute a
JOIN pg_class c     ON c.oid = a.attrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'conhecimento' AND a.attnum > 0 AND NOT a.attisdropped
ORDER BY c.relname, a.attnum;
