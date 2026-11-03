"""Cliente de embeddings da LogiTech, falando com o Ollama local.

Backend único de IA dos laboratórios, decisão registrada na ADR-005 do acervo.
Nenhuma chave de API, nenhum serviço remoto: o modelo roda no seu container.

O modelo é o `paraphrase-multilingual`, que devolve vetores de **768 dimensões**.
Essa dimensão não é uma escolha livre: ela é do modelo. Trocar o modelo de
embedding obriga a recriar a coluna `vector(768)` e a reindexar tudo, e é por
isso que ela aparece cravada no DDL do laboratório.

Ele não foi escolhido por reputação: foi escolhido **medindo neste acervo**. A
primeira versão deste laboratório usava o `nomic-embed-text`, e a medição de
`recall@3` sobre dez perguntas de contrato o reprovou. A tabela está no README,
na seção de valores de referência, e a lição vale mais do que o resultado:
modelo de embedding se escolhe medindo no seu corpus, não lendo a documentação
do fornecedor.

Não é tarefa. Este arquivo vem pronto.
"""

import json
import os
import urllib.error
import urllib.request

OLLAMA_URL = os.environ.get("LOGITECH_OLLAMA_URL", "http://localhost:11434")
MODELO = os.environ.get("LOGITECH_EMBEDDING_MODELO", "paraphrase-multilingual")

# Dimensão do paraphrase-multilingual. Está aqui como constante para o código
# poder reclamar cedo quando alguém trocar o modelo e esquecer de recriar a
# coluna. O `nomic-embed-text` também devolve 768, e é por isso que a troca
# entre os dois custou apenas uma reingestão.
DIMENSAO = 768

# Tempo limite generoso: a primeira chamada carrega o modelo na memória e é
# sempre a mais lenta da sessão. As seguintes voltam em dezenas de milissegundos.
TEMPO_LIMITE_S = 120


class ErroDeEmbedding(RuntimeError):
    """Falha ao obter vetores do Ollama. Separada de erro de banco de propósito:
    o conserto de uma e de outra é diferente."""


def _post(caminho: str, corpo: dict) -> dict:
    requisicao = urllib.request.Request(
        OLLAMA_URL.rstrip("/") + caminho,
        data=json.dumps(corpo).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(requisicao, timeout=TEMPO_LIMITE_S) as resposta:
            return json.loads(resposta.read().decode("utf-8"))
    except urllib.error.HTTPError as erro:
        detalhe = erro.read().decode("utf-8", "replace")[:300]
        raise ErroDeEmbedding(
            "o Ollama respondeu %s em %s: %s" % (erro.code, caminho, detalhe)
        ) from erro
    except (urllib.error.URLError, TimeoutError, OSError) as erro:
        raise ErroDeEmbedding(
            "não consegui falar com o Ollama em %s (%s). "
            "Suba com 'ollama serve' e confira 'ollama list'." % (OLLAMA_URL, erro)
        ) from erro


def vetorizar(textos: list[str]) -> list[list[float]]:
    """Devolve um vetor por texto, na mesma ordem da entrada.

    Usa a rota de lote `/api/embed`, que aceita uma lista e devolve uma lista.
    Vetorizar 60 trechos em uma chamada é muito mais rápido do que 60 chamadas,
    porque o custo de carregar o modelo é pago uma vez só.
    """
    if not textos:
        return []

    dados = _post("/api/embed", {"model": MODELO, "input": textos})
    vetores = dados.get("embeddings")

    if not vetores:
        # Ollama antigo só tem a rota unitária /api/embeddings. Caminho de
        # compatibilidade, uma chamada por texto.
        vetores = [
            _post("/api/embeddings", {"model": MODELO, "prompt": t})["embedding"]
            for t in textos
        ]

    for vetor in vetores:
        if len(vetor) != DIMENSAO:
            raise ErroDeEmbedding(
                "o modelo %s devolveu vetor de %d dimensões, e a coluna do banco "
                "é vector(%d). Ou troque o modelo, ou recrie a coluna e o índice."
                % (MODELO, len(vetor), DIMENSAO)
            )
    return vetores


def vetorizar_um(texto: str) -> list[float]:
    """Atalho para o caminho da pergunta, que é sempre um texto só."""
    return vetorizar([texto])[0]


def para_literal(vetor: list[float]) -> str:
    """Converte a lista Python no literal que o PostgreSQL entende como `vector`.

    O pgvector aceita a mesma notação de um array em texto: `[0.12,-0.03,...]`.
    A consulta faz o casting explícito com `%s::vector`. É por isso que este
    laboratório não precisa da biblioteca `pgvector` em Python: o tipo viaja
    como texto e o banco converte.
    """
    return "[" + ",".join(repr(float(x)) for x in vetor) + "]"
