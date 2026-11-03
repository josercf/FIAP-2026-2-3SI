-- ArenaLog: dois schemas, dois usuários, nenhum grant cruzado.
-- A senha é de laboratório. Não reutilize fora da sala.

CREATE USER elenco WITH PASSWORD 'elenco';
CREATE USER partidas WITH PASSWORD 'partidas';

CREATE SCHEMA elenco AUTHORIZATION elenco;
CREATE SCHEMA partidas AUTHORIZATION partidas;

REVOKE ALL ON SCHEMA elenco FROM PUBLIC;
REVOKE ALL ON SCHEMA partidas FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA elenco TO elenco;
GRANT USAGE, CREATE ON SCHEMA partidas TO partidas;

CREATE TABLE elenco.atletas (
    id UUID PRIMARY KEY,
    nome TEXT NOT NULL,
    campus TEXT NOT NULL,
    canal TEXT NOT NULL
);

CREATE TABLE partidas.desafios (
    id UUID PRIMARY KEY,
    atleta_id UUID NOT NULL,
    modalidade TEXT NOT NULL,
    descricao TEXT NOT NULL,
    campus TEXT NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    status TEXT NOT NULL,
    pontos INTEGER NOT NULL,
    faixa TEXT NOT NULL,
    janela_horas INTEGER NOT NULL,
    serie BOOLEAN NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL
);

ALTER TABLE elenco.atletas OWNER TO elenco;
ALTER TABLE partidas.desafios OWNER TO partidas;

GRANT SELECT, INSERT, UPDATE, DELETE ON elenco.atletas TO elenco;
GRANT SELECT, INSERT, UPDATE, DELETE ON partidas.desafios TO partidas;
