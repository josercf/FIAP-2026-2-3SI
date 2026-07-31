"""Serviço `rag` da plataforma LogiTech: FastAPI na porta 8010 (ADR-008).

Suba com:

    uvicorn rag.app:app --host 0.0.0.0 --port 8010 --reload

Rotas:

    GET  /health                   contrato da plataforma: 200 e {"status":"ok"}
    POST /api/v1/ingestao          relê contratos/ e regrava as duas tabelas
    POST /api/v1/busca             recuperação pura, sem modelo de linguagem
    POST /api/v1/perguntar         recuperação e geração, o RAG completo

`/api/v1/busca` existir separado de `/api/v1/perguntar` é decisão de projeto,
não conveniência: a busca é o que este laboratório mede e o que o verificador
confere. Poder olhar a recuperação sem a geração no caminho é o que permite
descobrir se uma resposta ruim veio de um trecho errado ou de um modelo fraco.

Não é tarefa. Este arquivo vem pronto.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import banco, geracao, ingestao
from .busca import buscar, montar_contexto
from .embeddings import MODELO, ErroDeEmbedding

app = FastAPI(
    title="LogiTech RAG",
    description="Busca semântica nos contratos de transporte da LogiTech.",
    version="1.0.0",
)


class Pergunta(BaseModel):
    pergunta: str = Field(min_length=3, max_length=1000)
    k: int = Field(default=5, ge=1, le=20)


@app.get("/health")
def saude():
    """Contrato da plataforma (ADR-006): todo serviço tem /health.

    Este devolve também a versão da extensão `vector`. Um serviço de RAG que
    responde `ok` com a extensão desligada está mentindo: a primeira busca vai
    falhar, e o `healthcheck` do Compose teria deixado passar.
    """
    versao = banco.extensao_ativa()
    return {
        "status": "ok",
        "servico": "rag",
        "extensao_vector": versao or "ausente",
        "modelo_embedding": MODELO,
    }


@app.post("/api/v1/ingestao")
def rodar_ingestao():
    try:
        return ingestao.ingerir(verboso=False)
    except ErroDeEmbedding as erro:
        raise HTTPException(status_code=503, detail=str(erro))
    except Exception as erro:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(erro))


@app.post("/api/v1/busca")
def rota_busca(entrada: Pergunta):
    """Recuperação pura. Nenhum modelo de linguagem gera texto aqui."""
    try:
        trechos = buscar(entrada.pergunta, entrada.k)
    except NotImplementedError as erro:
        raise HTTPException(status_code=501, detail=str(erro))
    except ErroDeEmbedding as erro:
        raise HTTPException(status_code=503, detail=str(erro))
    return {"pergunta": entrada.pergunta, "k": entrada.k, "trechos": trechos}


@app.post("/api/v1/perguntar")
def rota_perguntar(entrada: Pergunta):
    """RAG completo: recupera, aumenta o prompt e gera."""
    try:
        trechos = buscar(entrada.pergunta, entrada.k)
    except NotImplementedError as erro:
        raise HTTPException(status_code=501, detail=str(erro))
    except ErroDeEmbedding as erro:
        raise HTTPException(status_code=503, detail=str(erro))

    contexto = montar_contexto(trechos)
    resposta = geracao.responder(entrada.pergunta, contexto)

    return {
        "pergunta": entrada.pergunta,
        "resposta": resposta,
        "fontes": [
            {
                "n": i,
                "contrato": t["contrato"],
                "cliente": t["cliente"],
                "arquivo": t["arquivo"],
                "ordem": t["ordem"],
                "distancia": t["distancia"],
            }
            for i, t in enumerate(trechos, start=1)
        ],
    }
