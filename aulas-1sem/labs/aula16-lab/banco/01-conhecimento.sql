-- =====================================================================
-- Schema `conhecimento`, congelado da Aula 12.
-- =====================================================================
--
-- Roda uma única vez, na primeira subida de um volume de dados vazio: o
-- PostgreSQL executa tudo que estiver em /docker-entrypoint-initdb.d nessa
-- hora, e nunca mais. Se você já tinha o volume de outra aula, um
-- `docker compose down -v` é o que faz este arquivo rodar.
--
-- Na Aula 12 esta DDL era a tarefa, com lacunas. Aqui ela vem pronta: hoje o
-- assunto é integração, não modelagem.
--
-- Os schemas `pedidos` e `faturamento` NÃO aparecem aqui, de propósito. Eles
-- nascem do ORM de cada serviço, na subida: `ddl-auto` no lado Java e
-- `ModelBuilder` no lado C#. Ver os três lado a lado é bom conteúdo de banca.
-- =====================================================================

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
    -- A dimensão é do modelo, não uma escolha livre: o `paraphrase-multilingual`
    -- devolve 768 números. Trocar de modelo obriga a recriar esta coluna.
    embedding   vector(768),
    CONSTRAINT trechos_ordem_unica_por_contrato UNIQUE (contrato_id, ordem)
);

-- Índice de vizinhança aproximada, para o operador de distância de cosseno.
-- Criado com a classe de operadores certa: com a errada o índice nasce, ocupa
-- espaço e o planejador o ignora em silêncio.
CREATE INDEX IF NOT EXISTS trechos_embedding_hnsw
    ON conhecimento.trechos
 USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
