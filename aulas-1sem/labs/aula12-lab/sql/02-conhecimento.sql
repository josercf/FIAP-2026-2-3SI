-- =====================================================================
-- Passo 2: a DDL que nenhum ORM do curso escreve por você.
-- =====================================================================
--
-- Até aqui o schema nasceu do ORM. A partir daqui não nasce mais, e o motivo é
-- concreto: nem o Hibernate nem o EF Core sabem declarar uma coluna do tipo
-- `vector`. Ele vem de uma extensão, e extensão está fora do vocabulário do
-- mapeamento objeto-relacional.
--
-- São duas tabelas, e a normalização é deliberada (ADR-008). Uma tabela só
-- bastaria para o RAG funcionar, e é justamente por isso que são duas: o JOIN
-- entre elas é o que responde "de qual contrato veio este trecho", que é a
-- pergunta que separa um RAG utilizável de uma demonstração.
--
-- Rode assim, da raiz do laboratório:
--
--     docker compose exec -T postgres psql -U logitech -d logitech < sql/02-conhecimento.sql
--
-- Complete os `____` antes de rodar. O psql para no primeiro erro e diz a
-- linha.
-- =====================================================================


-- ---------------------------------------------------------------------
-- TODO-2a: ative a extensão de vetores.
-- ---------------------------------------------------------------------
-- A imagem `pgvector/pgvector:pg16` traz a extensão compilada e **disponível**,
-- e não instalada. Trocar a imagem do banco não dispensa este comando: ele é
-- por banco de dados, não por servidor.
--
-- Escreva a palavra-chave que falta. Depois de rodar, `\dx` mostra a extensão
-- na lista, e o tipo `vector` passa a existir.

CREATE ____ IF NOT EXISTS vector;


CREATE SCHEMA IF NOT EXISTS conhecimento;


-- ---------------------------------------------------------------------
-- TODO-2b: a tabela dos documentos.
-- ---------------------------------------------------------------------
-- Uma linha por contrato. Os campos vêm do cabeçalho YAML de cada arquivo em
-- `contratos/`.
--
--   2b-1  O tipo da chave primária. `bigserial` cria a coluna, a sequência e o
--         valor padrão de uma vez, que é o que o `GenerationType.IDENTITY` do
--         Hibernate produziu na tabela de pedidos que você leu no Passo 1.
--
--   2b-2  A restrição que impede o mesmo arquivo ser ingerido duas vezes. Ela
--         não é performance: é regra de negócio gravada no banco, como o
--         índice único de número de nota fiscal do Passo 1.

CREATE TABLE IF NOT EXISTS conhecimento.contratos (
    id        ____        PRIMARY KEY,
    cliente   varchar(160) NOT NULL,
    titulo    varchar(200) NOT NULL,
    vigencia  varchar(60)  NOT NULL,
    arquivo   varchar(200) NOT NULL ____,
    criado_em timestamptz  NOT NULL DEFAULT now()
);


-- ---------------------------------------------------------------------
-- TODO-2c: a tabela dos trechos.
-- ---------------------------------------------------------------------
-- Uma linha por pedaço de contrato, com o vetor do texto ao lado do texto.
--
--   2c-1  A chave estrangeira. Aponte `contrato_id` para a chave primária de
--         `conhecimento.contratos`. Acrescente `ON DELETE CASCADE`: apagar um
--         contrato precisa levar os trechos dele junto, senão a reingestão
--         deixa órfão no banco. A ingestão deste laboratório depende disso.
--
--   2c-2  A coluna do vetor. O tipo é `vector`, e a dimensão entre parênteses
--         **é a do modelo**, não uma escolha sua: o `paraphrase-multilingual`
--         devolve 768 números. Trocar por um modelo de outra dimensão obriga a
--         recriar esta coluna e a reindexar tudo. É a primeira decisão
--         irreversível deste laboratório.
--
--   2c-3  A restrição que impede dois trechos com a mesma ordem no mesmo
--         contrato. Repare que ela é sobre **duas colunas juntas**: ordem 3
--         pode existir em todos os contratos, mas só uma vez em cada.

CREATE TABLE IF NOT EXISTS conhecimento.trechos (
    id          bigserial PRIMARY KEY,
    contrato_id bigint    NOT NULL ____,
    ordem       int       NOT NULL,
    texto       text      NOT NULL,
    embedding   ____,
    CONSTRAINT trechos_ordem_unica_por_contrato ____ (contrato_id, ordem)
);


-- ---------------------------------------------------------------------
-- Confira o que você criou. Pelo psql, os atalhos são:
--
--     \dx                        a extensão vector aparece na lista
--     \dt conhecimento.*         as duas tabelas
--     \d+ conhecimento.trechos   a coluna embedding como vector(768) e a FK
--
-- E, sem atalho, a mesma coisa perguntada ao catálogo:
-- ---------------------------------------------------------------------

SELECT c.relname AS tabela, a.attname AS coluna,
       format_type(a.atttypid, a.atttypmod) AS tipo
FROM pg_attribute a
JOIN pg_class c     ON c.oid = a.attrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'conhecimento' AND a.attnum > 0 AND NOT a.attisdropped
ORDER BY c.relname, a.attnum;
