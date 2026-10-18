"""Ingestão: os contratos em Markdown viram linhas nas duas tabelas.

Roda uma vez, depois que você criou o schema `conhecimento` no Passo 2:

    python3 -m rag.ingestao          # a partir da raiz do laboratório

O que acontece, na ordem:

1. lê cada arquivo de `contratos/`;
2. separa o cabeçalho e grava **uma** linha em `conhecimento.contratos`;
3. divide o corpo em trechos (ver `rag/chunking.py`);
4. pede ao Ollama o vetor de cada trecho, em um único lote;
5. grava **uma linha por trecho** em `conhecimento.trechos`, com
   `contrato_id` apontando para a linha do passo 2.

O passo 5 é onde a normalização da ADR-008 se paga: cliente, título e vigência
ficam em `contratos`, uma vez cada, e não repetidos em cada um dos trechos.

Não é tarefa. Este arquivo vem pronto. Ele **falha de propósito** com uma
mensagem clara se você tentar rodá-lo antes de criar as tabelas: o Passo 2 vem
antes do Passo 3.
"""

import os
import sys
import time

import psycopg

from . import chunking
from .banco import conectar
from .embeddings import ErroDeEmbedding, para_literal, vetorizar

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_CONTRATOS = os.path.join(RAIZ, "contratos")


def carregar_arquivos() -> list[tuple[str, str]]:
    if not os.path.isdir(PASTA_CONTRATOS):
        raise SystemExit("não encontrei a pasta contratos/ em %s" % RAIZ)
    nomes = sorted(n for n in os.listdir(PASTA_CONTRATOS) if n.endswith(".md"))
    return [
        (nome, open(os.path.join(PASTA_CONTRATOS, nome), encoding="utf-8").read())
        for nome in nomes
    ]


def ingerir(verboso: bool = True) -> dict:
    arquivos = carregar_arquivos()
    inicio = time.monotonic()
    total_trechos = 0

    with conectar() as conexao:
        with conexao.cursor() as cursor:
            # Reingestão é idempotente: apaga tudo e refaz. O ON DELETE CASCADE
            # da chave estrangeira faz os trechos caírem junto com o contrato,
            # e é exatamente para isso que a restrição existe.
            cursor.execute("DELETE FROM conhecimento.contratos")

            for nome, bruto in arquivos:
                metadados, corpo = chunking.ler_cabecalho(bruto)
                trechos = chunking.dividir(corpo)

                cursor.execute(
                    """
                    INSERT INTO conhecimento.contratos (cliente, titulo, vigencia, arquivo)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        metadados.get("cliente", "(sem cliente)"),
                        metadados.get("titulo", nome),
                        metadados.get("vigencia", "(sem vigência)"),
                        nome,
                    ),
                )
                contrato_id = cursor.fetchone()[0]

                vetores = vetorizar(trechos)

                for ordem, (texto, vetor) in enumerate(zip(trechos, vetores), start=1):
                    cursor.execute(
                        """
                        INSERT INTO conhecimento.trechos (contrato_id, ordem, texto, embedding)
                        VALUES (%s, %s, %s, %s::vector)
                        """,
                        (contrato_id, ordem, texto, para_literal(vetor)),
                    )

                total_trechos += len(trechos)
                if verboso:
                    print("  %-34s %2d trechos" % (nome, len(trechos)))

        conexao.commit()

    decorrido = time.monotonic() - inicio
    return {
        "contratos": len(arquivos),
        "trechos": total_trechos,
        "segundos": round(decorrido, 2),
    }


def main() -> int:
    print("==> Ingerindo os contratos da LogiTech")
    try:
        resumo = ingerir()
    except psycopg.errors.UndefinedTable:
        print(
            "\nERRO: as tabelas de conhecimento ainda não existem.\n"
            "      O Passo 2 vem antes deste. Rode a sua DDL primeiro:\n"
            "        psql \"$LOGITECH_DB_URL\" -f sql/02-conhecimento.sql\n",
            file=sys.stderr,
        )
        return 1
    except psycopg.errors.UndefinedObject as erro:
        print(
            "\nERRO: o PostgreSQL não conhece o tipo `vector` (%s).\n"
            "      Falta o CREATE EXTENSION do TODO-2a, ou a imagem do banco não\n"
            "      é a pgvector/pgvector:pg16 do compose deste laboratório.\n" % erro,
            file=sys.stderr,
        )
        return 1
    except ErroDeEmbedding as erro:
        print("\nERRO de embedding: %s\n" % erro, file=sys.stderr)
        return 1

    print(
        "\n%d contratos, %d trechos, %.2f s."
        % (resumo["contratos"], resumo["trechos"], resumo["segundos"])
    )
    print("Anote TRECHOS_INGERIDOS e SEGUNDOS_DE_INGESTAO em docs/EVIDENCIAS.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
