"""Recuperação: a busca semântica, que é só mais um ORDER BY.

ESTE ARQUIVO TEM A LACUNA CENTRAL DO LABORATÓRIO (TODO-4).

A tese da aula está nas três linhas que você vai escrever aqui. Nada de banco
novo, nada de paradigma novo: a mesma tabela, o mesmo `SELECT`, o mesmo `JOIN`
do Passo 3. O que muda é **por qual expressão você ordena**. No Passo 3 era por
uma coluna; aqui é por uma distância calculada entre dois vetores.

Os três operadores de distância do pgvector:

    <=>   distância de cosseno       1 - similaridade de cosseno, faixa 0 a 2
    <->   distância euclidiana (L2)  a reta entre as duas pontas
    <#>   produto interno negativo   mais rápido, exige vetores normalizados

Para busca semântica em texto o padrão é `<=>`, porque o que interessa é o
**ângulo** entre os vetores, ou seja a direção do significado, e não o tamanho
deles. Dois trechos sobre o mesmo assunto apontam para o mesmo lado do espaço,
mesmo que um seja três vezes mais longo que o outro.

Distância menor significa mais parecido. Por isso é `ORDER BY ... ASC`, que é o
padrão do SQL, e não `DESC`: você quer o **mais próximo** no topo.
"""

from .banco import conectar
from .embeddings import para_literal, vetorizar_um

# ---------------------------------------------------------------------------
# TODO-4: complete a consulta de busca por similaridade.
#
#   TODO-4a  Junte `trechos` com `contratos`. É esse JOIN que responde
#            "de qual contrato veio este trecho", e é ele que permite citar a
#            fonte na resposta. Sem ele o RAG até funciona, e vira uma
#            demonstração: o usuário lê um parágrafo sem saber de onde saiu.
#
#   TODO-4b  Ordene pela distância entre o vetor da pergunta e o vetor do
#            trecho, usando o operador de distância de cosseno.
#            O vetor da pergunta chega como texto e precisa do casting
#            explícito: `%s::vector`.
#
#   TODO-4c  Traga só os k primeiros. Recuperação sem LIMIT não é recuperação:
#            é a tabela inteira ordenada, e o contexto do modelo não cabe nela.
#
# Os `%s` são preenchidos, na ordem, pela tupla de parâmetros lá embaixo.
# ---------------------------------------------------------------------------
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
____ conhecimento.contratos AS c ON c.id = t.contrato_id
ORDER BY ____
____ %s
"""


def _conferir_lacunas() -> None:
    """Recusa a consulta ainda com lacunas, com uma mensagem que diz o que fazer.

    Sem esta checagem o aluno receberia um erro de sintaxe do PostgreSQL
    apontando para a coluna 4 de uma linha com `____`, que é verdadeiro e
    inútil.
    """
    if "____" in CONSULTA_BUSCA:
        raise NotImplementedError(
            "TODO-4 ainda em aberto em rag/busca.py: a consulta de busca por "
            "similaridade tem lacunas. Complete o JOIN, o ORDER BY pela "
            "distância de cosseno e o LIMIT."
        )


def buscar(pergunta: str, k: int = 5) -> list[dict]:
    """Devolve os k trechos mais próximos da pergunta, do mais para o menos.

    Este é o R de RAG: **retrieval**. Repare que a única coisa que sai daqui
    são linhas de tabela. Nenhum modelo de linguagem foi chamado para gerar
    texto: o modelo entrou só na conversão da pergunta em vetor.
    """
    _conferir_lacunas()

    vetor = para_literal(vetorizar_um(pergunta))

    with conectar() as conexao, conexao.cursor() as cursor:
        cursor.execute(CONSULTA_BUSCA, (vetor, vetor, k))
        colunas = [d.name for d in cursor.description]
        linhas = [dict(zip(colunas, linha)) for linha in cursor.fetchall()]

    for linha in linhas:
        linha["distancia"] = round(float(linha["distancia"]), 6)
        # Similaridade de cosseno, para leitura humana: 1,0 é idêntico.
        linha["similaridade"] = round(1.0 - linha["distancia"], 6)
    return linhas


def montar_contexto(trechos: list[dict], limite_caracteres: int = 6000) -> str:
    """Concatena os trechos recuperados no bloco de contexto do prompt.

    Cada trecho entra rotulado com a sua origem. É esse rótulo que permite ao
    modelo citar o contrato, e é ele que sai do JOIN do TODO-4a.
    """
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
