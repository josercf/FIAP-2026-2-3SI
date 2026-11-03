"""Recuperação: a busca semântica, que é só mais um ORDER BY.

Versão **congelada** para a Aula 16: aqui a lacuna TODO-4 da Aula 12 já está
preenchida, porque hoje o assunto é integração, não recuperação. Vale ler as
três linhas com atenção mesmo assim:

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

import re

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


# ---------------------------------------------------------------------------
# Guardrail contra injeção INDIRETA (Aula 15, ADR-009)
#
# A injeção direta chega pela pergunta e o AI Gateway a intercepta. A indireta
# chega por aqui: alguém põe "ignore as instruções anteriores" dentro de um
# contrato, o RAG recupera aquele trecho por ser o mais próximo da pergunta, e
# a instrução do atacante entra no prompt como se fosse conteúdo confiável.
#
# O trecho recuperado é **dado**, nunca instrução. Neutralizá-lo aqui, antes de
# compor o prompt, é o que sustenta essa fronteira.
# ---------------------------------------------------------------------------

_INSTRUCAO_NO_DOCUMENTO = re.compile(
    r"(?:ignor\w*|desconsider\w*|esquec\w*|disregard|ignore|forget)"
    r"[^.\n]{0,40}(?:instru\w*|orienta\w*|regra\w*|prompt|instructions?)"
    r"|(?:^|\n)\s*(?:system|sistema|assistant|assistente)\s*[:>]"
    r"|<\|[^|>]{1,24}\|>",
    re.IGNORECASE,
)


def sanitizar_trecho(texto: str) -> tuple:
    """Devolve `(texto_neutralizado, quantas_instrucoes_foram_neutralizadas)`.

    Não apaga o trecho: substitui a instrução por um marcador visível. Apagar
    em silêncio esconderia do operador que alguém plantou instrução no acervo,
    que é exatamente o incidente que ele precisa enxergar.
    """
    achados = _INSTRUCAO_NO_DOCUMENTO.findall(texto)
    if not achados:
        return texto, 0
    return _INSTRUCAO_NO_DOCUMENTO.sub("[instrucao removida pelo guardrail]", texto), len(achados)


def montar_contexto(trechos: list[dict], limite_caracteres: int = 6000) -> str:
    """Concatena os trechos recuperados no bloco de contexto do prompt."""
    partes: list[str] = []
    tamanho = 0
    for i, trecho in enumerate(trechos, start=1):
        texto, neutralizados = sanitizar_trecho(trecho["texto"])
        trecho["instrucoes_neutralizadas"] = neutralizados
        bloco = "[%d] %s (%s), trecho %d:\n%s" % (
            i,
            trecho["contrato"],
            trecho["cliente"],
            trecho["ordem"],
            texto,
        )
        if tamanho + len(bloco) > limite_caracteres:
            break
        partes.append(bloco)
        tamanho += len(bloco)
    return "\n\n".join(partes)
