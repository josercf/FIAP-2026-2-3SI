"""Serviço `rag` da plataforma LogiTech: FastAPI na porta 8010 (ADR-008).

Suba com:

    uvicorn rag.app:app --host 0.0.0.0 --port 8010 --reload

Rotas:

    GET  /health                   aberta: 200 e {"status":"ok"}
    POST /api/v1/ingestao          ADMIN
    POST /api/v1/busca             qualquer papel autenticado
    POST /api/v1/perguntar         qualquer papel autenticado
    POST /api/v1/rag/perguntar     o mesmo, no caminho que a ADR-009 nomeia

As duas últimas são a mesma rota. `/api/v1/rag/perguntar` é o caminho que o
contrato de segurança da ADR-009 cita; `/api/v1/perguntar` é o que a Aula 12
publicou e o que o servidor MCP já chama. Manter as duas custa uma linha e
evita quebrar o cliente de quem fez a Aula 12.

`/api/v1/busca` existir separado de `/api/v1/perguntar` é decisão de projeto,
não conveniência: a busca é o que este laboratório mede e o que o verificador
confere. Poder olhar a recuperação sem a geração no caminho é o que permite
descobrir se uma resposta ruim veio de um trecho errado ou de um modelo fraco.

Não é tarefa. Este arquivo vem pronto.
"""

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import banco, geracao, ingestao, seguranca
from .busca import buscar, montar_contexto
from .embeddings import MODELO, ErroDeEmbedding

app = FastAPI(
    title="LogiTech RAG",
    description="Busca semântica nos contratos de transporte da LogiTech.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=seguranca.origens_cors(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def exigir(authorization, *papeis):
    """Traduz o resultado da validação em 401 ou 403, e nada mais.

    401 é "não sei quem você é". 403 é "sei quem você é e não é o bastante".
    Devolver 403 para quem não mandou token esconde do cliente que faltou
    autenticar; devolver 401 para quem mandou token bom manda o cliente
    tentar logar de novo à toa.
    """
    if not seguranca.ativa():
        return
    try:
        seguranca.exigir(authorization, *papeis)
    except seguranca.ErroDePapel as erro:
        raise HTTPException(status_code=403, detail=str(erro))
    except seguranca.ErroDeToken as erro:
        raise HTTPException(status_code=401, detail=str(erro))


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
        "auth_ativa": seguranca.ativa(),
    }


@app.post("/api/v1/ingestao")
def rodar_ingestao(authorization: str = Header(default=None)):
    exigir(authorization, "ADMIN")
    try:
        return ingestao.ingerir(verboso=False)
    except ErroDeEmbedding as erro:
        raise HTTPException(status_code=503, detail=str(erro))
    except Exception as erro:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(erro))


@app.post("/api/v1/busca")
def rota_busca(entrada: Pergunta, authorization: str = Header(default=None)):
    """Recuperação pura. Nenhum modelo de linguagem gera texto aqui."""
    exigir(authorization)
    try:
        trechos = buscar(entrada.pergunta, entrada.k)
    except NotImplementedError as erro:
        raise HTTPException(status_code=501, detail=str(erro))
    except ErroDeEmbedding as erro:
        raise HTTPException(status_code=503, detail=str(erro))
    return {"pergunta": entrada.pergunta, "k": entrada.k, "trechos": trechos}


@app.post("/api/v1/rag/perguntar")
@app.post("/api/v1/perguntar")
def rota_perguntar(entrada: Pergunta, authorization: str = Header(default=None)):
    """RAG completo: recupera, aumenta o prompt e gera."""
    exigir(authorization)
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
                "instrucoes_neutralizadas": t.get("instrucoes_neutralizadas", 0),
            }
            for i, t in enumerate(trechos, start=1)
        ],
    }
