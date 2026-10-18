-- =====================================================================
-- servicos/orm-gerado.sql
--
-- Isto NÃO foi escrito à mão. É a saída de
--
--     pg_dump --schema-only --no-owner --no-privileges -n pedidos -n faturamento
--
-- tirada de um PostgreSQL onde os serviços **reais** das Aulas 05 e 06
-- tinham acabado de subir: o de Pedidos, em Java, com
-- `spring.jpa.hibernate.ddl-auto=update`, e o de Faturamento, em C#, com
-- `banco.Database.EnsureCreated()` sobre o `FaturamentoDbContext`.
--
-- Cada linha daqui para baixo foi escrita por um ORM, não por uma pessoa.
-- É esta a SQL que você nunca viu, e é ela que o Passo 1 manda ler.
--
-- O Compose monta este arquivo em /docker-entrypoint-initdb.d/, então ele roda
-- sozinho na primeira subida de um volume vazio. Sem ele, o Passo 1 abriria um
-- banco sem tabela nenhuma para ler.
--
-- Três coisas para reparar, e nenhuma delas é acidente:
--
--   1. O EF Core manteve os nomes do C# como estão, em PascalCase, e por isso
--      precisou de aspas: `"PedidoId"`. Sem as aspas o PostgreSQL rebaixaria
--      tudo para minúsculas. Consequência prática: no psql,
--      `SELECT PedidoId FROM faturamento.faturas` falha, e
--      `SELECT "PedidoId" ...` funciona. O Hibernate escolheu o contrário e
--      converteu `enderecoEntrega` em `endereco_entrega`.
--
--   2. `peso_kg numeric(38,2)` veio de um `BigDecimal` sem precisão declarada
--      no código Java: o Hibernate não adivinha e usa o teto. Ao lado,
--      `"Valor" numeric(12,2)` veio de um `HasPrecision(12, 2)` explícito no
--      `ModelBuilder`. A mesma ideia de negócio, dois resultados diferentes,
--      porque um dos dois foi declarado.
--
--   3. O `CONSTRAINT pedidos_status_check` nasceu de um `enum` Java anotado
--      com `@Enumerated(EnumType.STRING)`. O banco passou a recusar qualquer
--      status fora da lista, mesmo que o defeito venha de outra aplicação
--      escrevendo na mesma tabela. Regra de negócio gravada no banco.
-- =====================================================================

--
-- PostgreSQL database dump
--


-- Dumped from database version 16.14 (Debian 16.14-1.pgdg12+1)
-- Dumped by pg_dump version 16.14 (Debian 16.14-1.pgdg12+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: faturamento; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA faturamento;


--
-- Name: pedidos; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA pedidos;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: faturas; Type: TABLE; Schema: faturamento; Owner: -
--

CREATE TABLE faturamento.faturas (
    "Id" character varying(36) NOT NULL,
    "PedidoId" character varying(36) NOT NULL,
    "Cliente" character varying(120) NOT NULL,
    "Valor" numeric(12,2) NOT NULL,
    "MeioPagamento" character varying(40) NOT NULL,
    "PrazoDias" integer NOT NULL,
    "NumeroNotaFiscal" character varying(30) NOT NULL,
    "EmitidaEm" timestamp with time zone NOT NULL
);


--
-- Name: pedidos; Type: TABLE; Schema: pedidos; Owner: -
--

CREATE TABLE pedidos.pedidos (
    id character varying(36) NOT NULL,
    cliente character varying(120) NOT NULL,
    criado_em timestamp(6) with time zone NOT NULL,
    destino character varying(160) NOT NULL,
    endereco_entrega character varying(240) NOT NULL,
    numero_nota_fiscal character varying(30),
    origem character varying(160) NOT NULL,
    peso_kg numeric(38,2) NOT NULL,
    status character varying(30) NOT NULL,
    tipo_cliente character varying(20) NOT NULL,
    valor numeric(38,2) NOT NULL,
    CONSTRAINT pedidos_status_check CHECK (((status)::text = ANY ((ARRAY['CRIADO'::character varying, 'AGUARDANDO_FATURAMENTO'::character varying, 'FATURADO'::character varying, 'EM_TRANSITO'::character varying, 'ENTREGUE'::character varying])::text[])))
);


--
-- Name: faturas PK_faturas; Type: CONSTRAINT; Schema: faturamento; Owner: -
--

ALTER TABLE ONLY faturamento.faturas
    ADD CONSTRAINT "PK_faturas" PRIMARY KEY ("Id");


--
-- Name: pedidos pedidos_pkey; Type: CONSTRAINT; Schema: pedidos; Owner: -
--

ALTER TABLE ONLY pedidos.pedidos
    ADD CONSTRAINT pedidos_pkey PRIMARY KEY (id);


--
-- Name: IX_faturas_NumeroNotaFiscal; Type: INDEX; Schema: faturamento; Owner: -
--

CREATE UNIQUE INDEX "IX_faturas_NumeroNotaFiscal" ON faturamento.faturas USING btree ("NumeroNotaFiscal");


--
-- Name: IX_faturas_PedidoId; Type: INDEX; Schema: faturamento; Owner: -
--

CREATE UNIQUE INDEX "IX_faturas_PedidoId" ON faturamento.faturas USING btree ("PedidoId");


--
-- PostgreSQL database dump complete
--


