"""
LogiTech Enterprise - AI Gateway.

O ponto único de entrada de toda a IA da plataforma. Nasce nesta aula
(ADR-006) e é consumido pelo agente de atendimento da Aula 08.

Rotas do contrato (ADR-006 e ADR-009):
    GET  /health                  aberta: saúde do próprio gateway
    POST /v1/chat/completions     qualquer papel autenticado
    GET  /v1/metricas             ADMIN

Versão da Aula 16: o gateway ganhou os guardrails da Aula 15 (`guardrails.py`)
e a validação de JWT da Aula 14 (`seguranca.py`). Os dois são governados por
variável de ambiente e nenhum deles altera o caminho feliz do gateway da
Aula 07.

Sobre `/health` e a saúde dos provedores
----------------------------------------
`/health` responde 200 mesmo com todos os provedores fora do ar, e isso é
deliberado. Saúde do gateway é "o processo está de pé e consegue receber
requisição". Saúde dos provedores é outra coisa, e aparece em `/v1/metricas`
e no campo `provedores` desta mesma rota.

Confundir as duas quebra o `healthcheck` do Compose pelo motivo errado: o
container seria reiniciado em laço por causa de uma credencial ausente, que
reiniciar não resolve.

Arquitetura, em uma linha por camada:
    app.py         HTTP, validação de entrada e tradução de erro em status
    fachada.py     Facade: a única porta que o resto da plataforma conhece
    roteamento.py  Strategy: qual provedor tentar, e em que ordem
    provedores.py  as implementações intercambiáveis (remoto e local)
    politicas.py   cache de respostas e limite de taxa
    metricas.py    os contadores que a rota de métricas devolve
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
import seguranca
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

    Imprimir a configuração é o que permite ao aluno confirmar, no
    `docker compose logs ai-gateway`, que a variável que ele pôs no YAML
    chegou de fato ao processo.
    """
    global gateway
    estrategia = escolher_estrategia()
    provedores = montar_provedores()
    cache = CacheDeRespostas()
    limitador = LimitadorDeTaxa()
    gateway = GatewayDeIA(provedores, estrategia, cache, limitador, Metricas())

    print("=== LogiTech Enterprise - AI Gateway ===", flush=True)
    print("[GATEWAY] estratégia de roteamento: %s" % estrategia.nome, flush=True)
    print("[GATEWAY] provedores: %s" % ", ".join(p.nome for p in provedores), flush=True)
    for nome, situacao in gateway.estado_dos_provedores().items():
        print("[GATEWAY]   %-8s %s" % (nome, situacao), flush=True)
    print("[GATEWAY] limite: %d requisições por minuto e por cliente"
          % limitador.limite, flush=True)
    print("[GATEWAY] cache: limiar de similaridade %.2f, validade %ds"
          % (cache.limiar, cache.ttl_s), flush=True)
    print("[GATEWAY] guardrails: %s" % ("ativos" if guardrails.ativos() else "DESLIGADOS"),
          flush=True)
    print("[GATEWAY] autenticação: %s" % ("exigida" if seguranca.ativa() else "DESLIGADA"),
          flush=True)
    yield


app = FastAPI(
    title="LogiTech - AI Gateway",
    version="1.0.0",
    description="Ponto único de entrada de IA da plataforma LogiTech Enterprise.",
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
        """A última fala do usuário é o que vai ao modelo.

        Gateway de verdade repassa a conversa inteira. Aqui basta a última
        pergunta: o que a aula ensina é a camada, não a gestão de contexto.
        """
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
        "provedores": gateway.estado_dos_provedores(),
        "guardrails_ativos": guardrails.ativos(),
        "auth_ativa": seguranca.ativa(),
    }


def _sem_permissao(erro, status):
    return JSONResponse(status_code=status, content={"error": {
        "message": str(erro),
        "type": "nao_autenticado" if status == 401 else "sem_permissao",
    }})


@app.post("/v1/chat/completions")
async def chat(pedido: PedidoDeChat,
               x_servico: str = Header(default="anonimo"),
               authorization: str = Header(default=None)):
    """Uma pergunta ao gateway, no formato que qualquer cliente OpenAI fala.

    O cabeçalho `X-Servico` identifica quem está chamando e é a chave do
    limite de taxa. Sem ele, um serviço com defeito consumiria a cota dos
    outros sete.

    A ordem importa e é a mesma de todo gateway sério: **autentica primeiro,
    inspeciona depois**. Não faz sentido gastar o filtro de injeção com quem
    nem deveria estar falando com o modelo.
    """
    if seguranca.ativa():
        try:
            seguranca.exigir(authorization)
        except seguranca.ErroDePapel as erro:
            return _sem_permissao(erro, 403)
        except seguranca.ErroDeToken as erro:
            return _sem_permissao(erro, 401)

    pergunta = pedido.pergunta()
    if not pergunta:
        return JSONResponse(status_code=400, content={
            "error": {"message": "nenhuma mensagem de usuário com conteúdo",
                      "type": "requisicao_invalida"}})

    # Guardrail de entrada. 422 e não 400: a requisição está bem formada, o
    # que foi recusado é o conteúdo dela. A distinção aparece no corpo com o
    # campo `recusado`, que é o contrato da ADR-009.
    try:
        guardrails.inspecionar_entrada(pergunta)
    except guardrails.EntradaRecusada as erro:
        gateway.metricas.registrar_recusa_de_guardrail(erro.regra)
        return JSONResponse(status_code=422, content={
            "recusado": True,
            "motivo": erro.motivo,
            "regra": erro.regra,
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
        # 503, não 500: o gateway está bem, quem não respondeu foi o mundo
        # lá fora. O motivo de cada provedor vai no corpo, para o aluno não
        # ter que caçar no log.
        return JSONResponse(status_code=503, content={"error": {
            "message": "nenhum provedor de IA respondeu",
            "type": "provedores_indisponiveis",
            "motivos": erro.motivos,
        }})

    # Guardrail de saída. O modelo pode ter visto dado sensível no contexto
    # que o RAG montou; mascarar aqui, no ponto único de saída, é o que
    # garante que nenhum serviço da plataforma precise lembrar de fazer isso.
    conteudo, mascarados = guardrails.mascarar_saida(resultado.conteudo)
    gateway.metricas.registrar_mascaramentos(mascarados)

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
        # Extensão da LogiTech: tudo que o formato da OpenAI não tem lugar
        # para dizer e a nossa operação precisa saber.
        "logitech": {
            "provedor": resultado.provedor,
            "cache": resultado.origem_do_cache or "erro",
            "similaridade": resultado.similaridade,
            "fallback": resultado.houve_fallback,
            "tentativas": resultado.tentativas,
            "duracao_ms": resultado.duracao_ms,
            "mascaramentos": mascarados,
        },
    }


@app.get("/v1/metricas")
def metricas(authorization: str = Header(default=None)):
    """Métricas são de operação, e operação é papel ADMIN (ADR-009)."""
    if seguranca.ativa():
        try:
            seguranca.exigir(authorization, "ADMIN")
        except seguranca.ErroDePapel as erro:
            return _sem_permissao(erro, 403)
        except seguranca.ErroDeToken as erro:
            return _sem_permissao(erro, 401)

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
