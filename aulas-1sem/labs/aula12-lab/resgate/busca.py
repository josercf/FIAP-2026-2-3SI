"""Resgate do Passo 4: a busca por similaridade completa.

    cp resgate/busca.py rag/busca.py

O único bloco que muda em relação ao arquivo com lacunas é a constante
`CONSULTA_BUSCA`. Vale ler as três linhas com atenção antes de copiar:

    JOIN conhecimento.contratos AS c ON c.id = t.contrato_id
        traz o contrato de origem de cada trecho, e é o que permite citar a
        fonte na resposta;

    ORDER BY t.embedding <=> %s::vector
        ordena por distância de cosseno, do mais próximo para o mais distante.
        Ascendente, que é o padrão do SQL: distância menor significa mais
        parecido;

    LIMIT %s
        corta no k pedido. O vetor da pergunta aparece duas vezes na tupla de
        parâmetros porque o mesmo literal é usado na coluna de distância e na
        expressão de ordenação.
"""

from .banco import conectar
from .embeddings import para_literal, vetorizar_um

CONSULTA_BUSCA = """
SELECT
    t.id,
    t.ordem,
    t.texto,
    c.cliente,
    c.titulo   AS contrato,
    c.arquivo,
    t.embedding <=> %s::vector AS distancia
FROM conhecimento.trechos AS t
JOIN conhecimento.contratos AS c ON c.id = t.contrato_id
ORDER BY t.embedding <=> %s::vector
LIMIT %s
"""


def _conferir_lacunas() -> None:
    if "____" in CONSULTA_BUSCA:
        raise NotImplementedError(
            "TODO-4 ainda em aberto em rag/busca.py: a consulta de busca por "
            "similaridade tem lacunas. Complete o JOIN, o ORDER BY pela "
            "distância de cosseno e o LIMIT."
        )


def buscar(pergunta: str, k: int = 5) -> list[dict]:
    """Devolve os k trechos mais próximos da pergunta, do mais para o menos."""
    _conferir_lacunas()

    vetor = para_literal(vetorizar_um(pergunta))

    with conectar() as conexao, conexao.cursor() as cursor:
        cursor.execute(CONSULTA_BUSCA, (vetor, vetor, k))
        colunas = [d.name for d in cursor.description]
        linhas = [dict(zip(colunas, linha)) for linha in cursor.fetchall()]

    for linha in linhas:
        linha["distancia"] = round(float(linha["distancia"]), 6)
        linha["similaridade"] = round(1.0 - linha["distancia"], 6)
    return linhas


def montar_contexto(trechos: list[dict], limite_caracteres: int = 6000) -> str:
    """Concatena os trechos recuperados no bloco de contexto do prompt."""
    partes: list[str] = []
    tamanho = 0
    for i, trecho in enumerate(trechos, start=1):
        bloco = "[%d] %s (%s), trecho %d:\n%s" % (
            i,
            trecho["contrato"],
            trecho["cliente"],
            trecho["ordem"],
            trecho["texto"],
        )
        if tamanho + len(bloco) > limite_caracteres:
            break
        partes.append(bloco)
        tamanho += len(bloco)
    return "\n\n".join(partes)
