"""
LogiTech Enterprise - AI Gateway, endurecido (Aula 15).

O gateway é o mesmo da Aula 07. O que muda aqui é que ele deixou de ser só o
ponto único de **entrada** de IA e passou a ser o ponto único de **controle**:
toda pergunta que vai a um modelo e toda resposta que volta atravessam a
camada de `guardrails.py`.

Rotas do contrato (ADR-006 e ADR-009):
    GET  /health                  saúde do próprio gateway
    POST /v1/chat/completions     formato compatível com OpenAI
    GET  /v1/metricas             cache, provedores, fallback e guardrail

Este arquivo **não é tarefa**. A ligação entre o HTTP e os guardrails já está
escrita, e é de propósito: o que a aula cobra é a política, em
`guardrails.py`, não o encanamento. Leia mesmo assim, porque a ordem das
chamadas aqui é conteúdo.

A ordem, e por que ela é essa
-----------------------------
    1. guardrail de entrada    antes do limite de taxa e antes do cache
    2. limite de taxa
    3. cache
    4. roteamento e fallback
    5. guardrail de saída      depois de tudo, inclusive depois do cache

O guardrail de entrada vem **antes do cache** porque uma injeção que passou
uma vez com o guardrail desligado fica guardada, e serviria de novo, já pronta,
com o guardrail ligado. Filtro que roda depois do cache protege a primeira
vítima e nenhuma das seguintes.

O guardrail de saída vem **depois do cache** pelo mesmo motivo, invertido: uma
resposta gravada antes de o mascaramento existir continuaria vazando CPF a cada
acerto de cache se a máscara fosse aplicada só na hora de gravar.

O 422 e o porquê dele
---------------------
Entrada recusada devolve **422** e não 400. O 400 diz "não entendi a sua
requisição"; aqui a requisição está perfeitamente bem formada e foi entendida.
O que houve foi recusa semântica: o conteúdo é processável e a política diz
não. É a mesma diferença entre 401 e 403, que a Aula 14 estabeleceu.
"""

from __future__ import annotations

import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import guardrails
from fachada import GatewayDeIA, TodosOsProvedoresIndisponiveis
from metricas import Metricas
from politicas import CacheDeRespostas, LimitadorDeTaxa, LimiteExcedido
from provedores import montar_provedores
from roteamento import escolher_estrategia

INICIADO_EM = time.time()
gateway: GatewayDeIA


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    """Monta o gateway na subida e anuncia a configuração escolhida.

    A linha do guardrail no log de subida não é enfeite: é como o aluno
    confirma, no `docker compose logs ai-gateway`, que o
    `LOGITECH_GUARDRAILS_ATIVOS` que ele pôs no YAML chegou ao processo. Mais
    de uma sessão de depuração deste laboratório termina aqui.
    """
    global gateway
    estrategia = escolher_estrategia()
    provedores = montar_provedores()
    cache = CacheDeRespostas()
    limitador = LimitadorDeTaxa()
    gateway = GatewayDeIA(provedores, estrategia, cache, limitador, Metricas())

    print("=== LogiTech Enterprise - AI Gateway (Aula 15) ===", flush=True)
    print("[GATEWAY] estratégia de roteamento: %s" % estrategia.nome, flush=True)
    print("[GATEWAY] provedores: %s" % ", ".join(p.nome for p in provedores), flush=True)
    print("[GUARDRAIL] %s" % ("ATIVOS" if guardrails.ativos()
                              else "DESLIGADOS (LOGITECH_GUARDRAILS_ATIVOS=false)"),
          flush=True)
    yield


app = FastAPI(
    title="LogiTech - AI Gateway",
    version="2.0.0",
    description="Ponto único de entrada e de controle de IA da LogiTech.",
    lifespan=ciclo_de_vida,
)


# ---------------------------------------------------------------------------
# Contrato de entrada e saída, no formato da OpenAI
# ---------------------------------------------------------------------------


class Mensagem(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class PedidoDeChat(BaseModel):
    messages: list[Mensagem] = Field(min_length=1)
    model: str | None = None
    temperature: float | None = None

    def pergunta(self) -> str:
        """A última fala do usuário é o que vai ao modelo."""
        for mensagem in reversed(self.messages):
            if mensagem.role == "user":
                return mensagem.content.strip()
        return self.messages[-1].content.strip()


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------


@app.get("/health")
def health():
    return {
        "status": "ok",
        "servico": "ai-gateway",
        "uptime_s": int(time.time() - INICIADO_EM),
        "estrategia": gateway.estrategia.nome,
        "guardrails_ativos": guardrails.ativos(),
        "provedores": gateway.estado_dos_provedores(),
    }


@app.post("/v1/chat/completions")
async def chat(pedido: PedidoDeChat,
               x_servico: str = Header(default="anonimo")):
    """Uma pergunta ao gateway, no formato que qualquer cliente OpenAI fala."""
    pergunta = pedido.pergunta()
    if not pergunta:
        return JSONResponse(status_code=400, content={
            "error": {"message": "nenhuma mensagem de usuário com conteúdo",
                      "type": "requisicao_invalida"}})

    # 1. Guardrail de entrada (ADR-009, seção 6): 422 com recusado e motivo.
    if guardrails.ativos():
        veredito = guardrails.inspecionar_entrada(pergunta)
        if veredito.recusado:
            gateway.metricas.registrar_recusa_de_entrada(veredito.regra)
            print("[GUARDRAIL] entrada recusada pela regra '%s': %s"
                  % (veredito.regra, pergunta[:120].replace("\n", " ")), flush=True)
            return JSONResponse(status_code=422, content={
                "recusado": True,
                "motivo": veredito.motivo,
                "regra": veredito.regra,
                "guardrail": "entrada",
            })

    try:
        resultado = await gateway.responder(pergunta, pedido.model, x_servico)
    except LimiteExcedido as erro:
        gateway.metricas.registrar_recusa_por_limite()
        return JSONResponse(
            status_code=429,
            headers={"Retry-After": str(erro.segundos_para_liberar)},
            content={"error": {
                "message": str(erro),
                "type": "limite_de_taxa",
                "cliente": x_servico,
                "retry_after_s": erro.segundos_para_liberar,
            }})
    except TodosOsProvedoresIndisponiveis as erro:
        return JSONResponse(status_code=503, content={"error": {
            "message": "nenhum provedor de IA respondeu",
            "type": "provedores_indisponiveis",
            "motivos": erro.motivos,
        }})

    # 2. Guardrail de saída: mascarar antes de devolver.
    conteudo = resultado.conteudo
    mascarados = 0
    if guardrails.ativos():
        conteudo, mascarados = guardrails.mascarar_saida(conteudo)
        if mascarados:
            gateway.metricas.registrar_mascaramento(mascarados)
            print("[GUARDRAIL] %d dado(s) sensível(is) mascarado(s) na saída"
                  % mascarados, flush=True)

    return {
        "id": "chatcmpl-%s" % uuid.uuid4().hex[:24],
        "object": "chat.completion",
        "created": int(time.time()),
        "model": resultado.modelo,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": conteudo},
            "finish_reason": "stop",
        }],
        "usage": {"total_tokens": resultado.tokens_estimados},
        "logitech": {
            "provedor": resultado.provedor,
            "cache": resultado.origem_do_cache or "erro",
            "similaridade": resultado.similaridade,
            "fallback": resultado.houve_fallback,
            "tentativas": resultado.tentativas,
            "duracao_ms": resultado.duracao_ms,
            "guardrail": {
                "ativos": guardrails.ativos(),
                "mascaramentos": mascarados,
            },
        },
    }


@app.get("/v1/metricas")
def metricas():
    return gateway.metricas.instantaneo(
        entradas_em_cache=len(gateway.cache),
        limite_por_minuto=gateway.limitador.limite,
        estrategia=gateway.estrategia.nome,
        guardrails_ativos=guardrails.ativos(),
    )


@app.exception_handler(404)
async def nao_encontrada(request: Request, _):
    return JSONResponse(status_code=404, content={"error": {
        "message": "rota não encontrada",
        "rota": request.url.path,
        "disponiveis": ["/health", "/v1/chat/completions", "/v1/metricas"],
    }})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("LOGITECH_PORTA", "4000")),
        log_level="warning",
    )
