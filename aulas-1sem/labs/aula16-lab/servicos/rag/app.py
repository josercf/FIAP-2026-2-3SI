"""
LogiTech Enterprise - serviço de RAG sobre os contratos de transporte.

Não é tarefa, tirando o `composicao.py` que ele chama. Leia mesmo assim: a
topologia deste arquivo é conteúdo da aula.

Rotas (ADR-008 e ADR-009):
    GET  /health
    POST /api/v1/rag/perguntar    {"pergunta": "...", "k": 3}

O RAG não fala com o Ollama
---------------------------
Repare para onde este serviço manda a pergunta: para o **AI Gateway**, na porta
4000, e não para o Ollama. É a ADR-007 valendo, e na Aula 15 ela vira decisão de
segurança, não só de arquitetura.

Se o RAG falasse direto com o modelo, o guardrail de saída do gateway não veria
esta resposta, e o CPF que o Passo 2 mostra vazando sairia inteiro por aqui.
Um único caminho até o modelo é o que permite uma única política.

Sobram duas camadas, e elas não são redundantes:

    RAG      sanitiza o **documento** antes de compor o prompt   (TODO-4)
    Gateway  inspeciona a **pergunta** e mascara a **resposta**  (TODO-1, TODO-2)

O gateway não pode fazer o trabalho do RAG: para ele, o prompt composto chega
como uma pergunta só, e recusá-la com 422 negaria atendimento a um cliente que
não fez nada de errado. Quem sabe qual pedaço do texto é documento e qual é
pergunta é quem montou o prompt.
"""

from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import composicao
import recuperacao

INICIADO_EM = time.time()
GATEWAY = os.environ.get("LOGITECH_GATEWAY_URL", "http://ai-gateway:4000")
PASTA = Path(os.environ.get("LOGITECH_CONTRATOS", "/app/contratos"))
TEMPO_LIMITE = float(os.environ.get("LOGITECH_IA_TIMEOUT_LOCAL_S", "180"))

VERDADEIROS = frozenset({"1", "true", "sim", "on", "yes"})

ACERVO: list[recuperacao.Trecho] = []


def guardrails_ativos() -> bool:
    """O mesmo interruptor do gateway, lido aqui também (ADR-009, seção 6)."""
    return os.environ.get("LOGITECH_GUARDRAILS_ATIVOS", "true").strip().lower() in VERDADEIROS


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    """Carrega o acervo uma vez, na subida.

    `lifespan`, e não `@app.on_event("startup")`: o decorador está depreciado
    desde o FastAPI 0.109, e o TODO-5b sobe a versão desta imagem. Corrigir CVE
    de dependência costuma trazer junto um pedaço de código depreciado, e
    descobrir isso agora é melhor do que descobrir na Aula 16.
    """
    global ACERVO
    ACERVO = recuperacao.carregar(PASTA)
    print("=== LogiTech Enterprise - RAG de contratos (Aula 15) ===", flush=True)
    print("[RAG] %d trechos carregados de %s" % (len(ACERVO), PASTA), flush=True)
    print("[RAG] gateway: %s" % GATEWAY, flush=True)
    print("[GUARDRAIL] %s" % ("ATIVOS" if guardrails_ativos() else "DESLIGADOS"),
          flush=True)
    yield


app = FastAPI(title="LogiTech - RAG de contratos", version="2.0.0",
              lifespan=ciclo_de_vida)


class Pergunta(BaseModel):
    pergunta: str = Field(min_length=1)
    k: int = Field(default=3, ge=1, le=8)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "servico": "rag",
        "uptime_s": int(time.time() - INICIADO_EM),
        "trechos": len(ACERVO),
        "guardrails_ativos": guardrails_ativos(),
    }


@app.post("/api/v1/rag/perguntar")
async def perguntar(entrada: Pergunta):
    trechos = recuperacao.recuperar(entrada.pergunta, ACERVO, entrada.k)
    if not trechos:
        return JSONResponse(status_code=404, content={
            "error": {"message": "nenhum trecho de contrato casou com a pergunta"}})

    removidos: list[str] = []
    if guardrails_ativos():
        prompt, removidos = composicao.compor_prompt(entrada.pergunta, trechos)
    else:
        prompt = composicao.compor_ingenuo(entrada.pergunta, trechos)

    try:
        async with httpx.AsyncClient(timeout=TEMPO_LIMITE) as cliente:
            resposta = await cliente.post(
                "%s/v1/chat/completions" % GATEWAY.rstrip("/"),
                headers={"X-Servico": "rag"},
                json={"messages": [{"role": "user", "content": prompt}]},
            )
    except httpx.HTTPError as erro:
        return JSONResponse(status_code=503, content={"error": {
            "message": "o AI Gateway não respondeu em %s (%s)"
                       % (GATEWAY, type(erro).__name__)}})

    if resposta.status_code == 422:
        # O gateway recusou o prompt composto. Acontece, e é informação: quer
        # dizer que o documento envenenado passou pela sanitização do RAG e
        # ainda parecia ataque para o guardrail de entrada.
        return JSONResponse(status_code=422, content={
            "recusado": True,
            "onde": "ai-gateway",
            "detalhe": resposta.json(),
            "fontes": [t.como_dicionario() for t in trechos],
        })

    if resposta.status_code != 200:
        return JSONResponse(status_code=502, content={"error": {
            "message": "o AI Gateway respondeu HTTP %d" % resposta.status_code,
            "corpo": resposta.text[:400]}})

    corpo = resposta.json()
    return {
        "resposta": corpo["choices"][0]["message"]["content"],
        "fontes": [
            {"arquivo": t.arquivo, "cliente": t.cliente,
             "clausula": t.clausula, "nota": round(t.nota, 4)}
            for t in trechos
        ],
        "guardrail": {
            "ativos": guardrails_ativos(),
            "paragrafos_removidos": removidos,
            "mascaramentos_no_gateway": corpo.get("logitech", {})
                                             .get("guardrail", {})
                                             .get("mascaramentos", 0),
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0",
                port=int(os.environ.get("LOGITECH_PORTA", "8010")),
                log_level="warning")
