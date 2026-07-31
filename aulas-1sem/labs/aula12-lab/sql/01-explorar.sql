-- =====================================================================
-- Passo 1: leia a SQL que escreveram por você.
-- =====================================================================
--
-- Você persistiu em PostgreSQL o semestre inteiro sem escrever uma linha de
-- SQL. No serviço de Pedidos, em Java, o schema nasceu de
-- `spring.jpa.hibernate.ddl-auto=update`. No de Faturamento, em C#, nasceu do
-- `OnModelCreating` do EF Core. Os dois estão corretos para o que a Aula 05
-- ensina, que é Repository Pattern. A consequência é que ninguém nunca viu o
-- que saiu do outro lado.
--
-- Este arquivo não tem lacuna e não é para ser executado de uma vez. É um
-- roteiro de exploração: abra o `psql` e rode comando a comando, lendo a
-- saída. O que você vai ler é DDL de verdade, gerada por dois ORMs diferentes
-- sobre o mesmo banco.
--
--     docker compose up -d postgres
--     docker compose exec postgres psql -U logitech -d logitech
--
-- Os comandos que começam com barra invertida são do `psql`, não do SQL. Eles
-- não funcionam em cliente gráfico nem dentro de um `SELECT`: são atalhos que
-- o cliente traduz em consultas ao catálogo do PostgreSQL.
-- =====================================================================


-- ---------------------------------------------------------------------
-- 1.1  Que schemas existem neste banco?
-- ---------------------------------------------------------------------
-- Atalho do psql:  \dn
--
-- Você deve ver `pedidos` e `faturamento`, um por Bounded Context, como manda
-- o contrato da plataforma (ADR-006). E ainda NÃO deve ver `conhecimento`:
-- ele é o que você cria no Passo 2.

SELECT nspname AS schema
FROM pg_namespace
WHERE nspname NOT LIKE 'pg\_%' AND nspname <> 'information_schema'
ORDER BY nspname;


-- ---------------------------------------------------------------------
-- 1.2  Que tabelas cada ORM criou?
-- ---------------------------------------------------------------------
-- Atalhos do psql:  \dt pedidos.*    e    \dt faturamento.*

SELECT schemaname AS schema, tablename AS tabela
FROM pg_tables
WHERE schemaname IN ('pedidos', 'faturamento')
ORDER BY schemaname, tablename;


-- ---------------------------------------------------------------------
-- 1.3  A anatomia de uma tabela que você não escreveu
-- ---------------------------------------------------------------------
-- Atalho do psql:  \d+ faturamento.faturas
--
-- Repare no que o `ModelBuilder` do EF Core produziu a partir de três linhas
-- de C#:
--
--     fatura.Property(f => f.Cliente).HasMaxLength(120).IsRequired();
--       ->  cliente character varying(120) NOT NULL
--
--     fatura.Property(f => f.Valor).HasPrecision(12, 2);
--       ->  valor numeric(12,2)
--
--     fatura.HasIndex(f => f.NumeroNotaFiscal).IsUnique();
--       ->  CREATE UNIQUE INDEX ... ON faturamento.faturas (numero_nota_fiscal)
--
-- Cada linha de configuração do ORM virou uma decisão de schema. O ORM não
-- inventou nada: ele traduziu. E o que ele traduz é exatamente a linguagem que
-- você vai escrever no Passo 2.

SELECT column_name AS coluna,
       data_type   AS tipo,
       character_maximum_length AS tamanho,
       numeric_precision AS precisao,
       numeric_scale     AS escala,
       is_nullable AS aceita_nulo
FROM information_schema.columns
WHERE table_schema = 'faturamento' AND table_name = 'faturas'
ORDER BY ordinal_position;


-- ---------------------------------------------------------------------
-- 1.4  Os índices e as restrições que vieram de brinde
-- ---------------------------------------------------------------------
-- Atalho do psql:  \di faturamento.*
--
-- Índice único não é performance: é **regra de negócio gravada no banco**.
-- O `HasIndex(...).IsUnique()` do EF Core diz "não existem duas faturas com o
-- mesmo número de nota fiscal", e o banco passa a recusar a segunda inserção,
-- mesmo que o código da aplicação tenha um bug.

SELECT indexname AS indice, indexdef AS definicao
FROM pg_indexes
WHERE schemaname IN ('pedidos', 'faturamento')
ORDER BY schemaname, indexname;


-- ---------------------------------------------------------------------
-- 1.5  O tipo `vector` já existe neste banco?
-- ---------------------------------------------------------------------
-- Ainda não. A imagem `pgvector/pgvector:pg16` traz a extensão **compilada e
-- disponível**, e não instalada. Instalar é o TODO-2a do próximo arquivo.
--
-- A consulta abaixo devolve zero linhas agora e uma linha depois do Passo 2.

SELECT extname AS extensao, extversion AS versao
FROM pg_extension
ORDER BY extname;


-- ---------------------------------------------------------------------
-- Registre em docs/EVIDENCIAS.md, antes de passar ao Passo 2:
--
--   SCHEMAS_QUE_O_ORM_CRIOU
--   TIPO_DA_COLUNA_VALOR         (o que o HasPrecision(12,2) virou)
--   INDICES_QUE_NAO_ESCREVI      (quantos, e o que cada um garante)
-- ---------------------------------------------------------------------
