"""Conexão com o PostgreSQL da plataforma LogiTech.

Endereço nunca cravado no código: vem de `LOGITECH_DB_URL`, com padrão de
desenvolvimento local. Mesma regra do contrato da plataforma (ADR-006) que o
serviço de Pedidos em Java e o de Faturamento em C# já seguem.

Uma diferença que vale notar, e que é conteúdo da aula: lá o schema nasce do
ORM (`ddl-auto=update` no Hibernate, `ModelBuilder` no EF Core). Aqui não há
ORM nenhum, e o schema `conhecimento` nasce da DDL que você escreve no
Passo 2. Nenhum ORM do curso declara uma coluna `vector`.

Não é tarefa. Este arquivo vem pronto.
"""

import os

import psycopg

# Forma libpq da URL. O contrato da plataforma fixa o **nome** da variável;
# cada stack a escreve na sintaxe que a sua biblioteca exige, e esta é a do
# psycopg. No Java a mesma variável vale um `jdbc:postgresql://...`.
DB_URL = os.environ.get(
    "LOGITECH_DB_URL", "postgresql://logitech:logitech@localhost:5432/logitech"
)

SCHEMA = "conhecimento"


def conectar():
    """Abre uma conexão nova. Uso: `with conectar() as conexao: ...`.

    O `search_path` já entra apontando para o schema `conhecimento`, o que
    permite escrever `trechos` em vez de `conhecimento.trechos` nas consultas
    deste serviço. Um schema por Bounded Context, e ninguém lê a tabela do
    outro: este serviço nunca enxerga `pedidos` nem `faturamento`.
    """
    conexao = psycopg.connect(DB_URL, connect_timeout=10)
    with conexao.cursor() as cursor:
        cursor.execute("SET search_path TO %s, public" % SCHEMA)
    return conexao


def extensao_ativa() -> str | None:
    """Devolve a versão da extensão `vector`, ou None quando ela não foi criada.

    Serve ao `GET /health`: um serviço de RAG que responde `ok` com a extensão
    desligada está mentindo, porque a primeira busca vai falhar.
    """
    try:
        with conectar() as conexao, conexao.cursor() as cursor:
            cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            linha = cursor.fetchone()
            return linha[0] if linha else None
    except psycopg.Error:
        return None
