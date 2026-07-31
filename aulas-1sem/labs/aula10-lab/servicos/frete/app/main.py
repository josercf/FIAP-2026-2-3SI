"""API HTTP do serviço de frete da LogiTech (FastAPI, porta 8000).

CONGELADO. Não é tarefa da Aula 10.

Este é o serviço da Aula 06 com as lacunas daquele laboratório já
preenchidas, mais duas coisas que a ADR-008 acrescentou para hoje:

1. **CORS ligado**, lendo `LOGITECH_CORS_ORIGINS`. Até a Aula 08 todo
   consumidor desta API era outro processo de servidor, e servidor ignora a
   política de mesma origem. A partir de hoje quem chama é o navegador do
   cliente da LogiTech, e sem este bloco o Portal recebe a resposta e o
   navegador a joga fora antes de o React ver qualquer coisa.

2. A rota `POST /api/v1/frete/cotacao/pedido`, que cota o frete de um pedido
   que já existe. Ela delega para `CotadorDePedido`, que consulta o serviço
   de Pedidos para saber o peso. É essa colaboração que os seus testes de
   unidade de hoje precisam dublar.

Para subir:

    cd servicos/frete && uvicorn app.main:app --port 8000 --reload

Documentação OpenAPI gerada pelo Pydantic: http://localhost:8000/docs
"""

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .cliente_pedidos import (
    ClientePedidosHttp,
    PedidoNaoEncontrado,
    PedidosIndisponivel,
)
from .cotador import (
    CargaAcimaDoLimite,
    CotadorDePedido,
    ModalidadeNaoSuportada,
    PedidoInvalido,
)
from .distancias import TabelaDistancias
from .modelos import (
    CotacaoDePedidoPedida,
    PedidoCotacao,
    RespostaCotacao,
    RespostaCotacaoDePedido,
    RespostaSaude,
)
from .registro import modalidades, obter

CORS_PADRAO = "http://localhost:5173,http://localhost:4200"

app = FastAPI(
    title="LogiTech Frete",
    version="2.0.0",
    description="Motor de cálculo de frete da LogiTech Enterprise AI Platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in
                   os.getenv("LOGITECH_CORS_ORIGINS", CORS_PADRAO).split(",")
                   if o.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

TABELA = TabelaDistancias()


@app.get("/health", response_model=RespostaSaude, tags=["infraestrutura"])
def saude() -> RespostaSaude:
    """Sonda de saúde exigida pela ADR-006."""
    return RespostaSaude(status="ok")


@app.get("/api/v1/frete/modalidades", tags=["frete"])
def listar_modalidades() -> dict[str, list[str]]:
    """As modalidades que o registro conhece."""
    return {"modalidades": modalidades()}


@app.post("/api/v1/frete/cotacao", response_model=RespostaCotacao, tags=["frete"])
def cotar(pedido: PedidoCotacao) -> RespostaCotacao:
    """Cotação avulsa: o cliente informa origem, destino e peso.

    É esta a rota que o Portal do Cliente usa na tela de simulação, e ela
    não fala com o serviço de Pedidos: tudo o que ela precisa veio no corpo
    da requisição.
    """
    try:
        estrategia = obter(pedido.modalidade)
    except KeyError as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from None

    cotacao = estrategia.cotar(TABELA.km(pedido.origem, pedido.destino),
                               pedido.pesoKg)
    return RespostaCotacao(valor=cotacao.valor, prazoDias=cotacao.prazo_dias,
                           modalidade=cotacao.modalidade)


@app.post("/api/v1/frete/cotacao/pedido", response_model=RespostaCotacaoDePedido,
          tags=["frete"])
def cotar_pedido(entrada: CotacaoDePedidoPedida) -> RespostaCotacaoDePedido:
    """Recotação de um pedido existente. Consulta o serviço de Pedidos.

    Repare que o cotador é construído **aqui**, na borda HTTP, recebendo o
    cliente HTTP de verdade. Nos seus testes ele será construído com um
    dublê no lugar, e nenhuma linha de `cotador.py` muda por causa disso.
    """
    cotador = CotadorDePedido(ClientePedidosHttp(), tabela=TABELA)
    try:
        resultado = cotador.cotar(entrada.pedidoId, entrada.modalidade)
    except PedidoInvalido as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from None
    except ModalidadeNaoSuportada as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from None
    except CargaAcimaDoLimite as erro:
        raise HTTPException(status_code=409, detail=str(erro)) from None
    except PedidoNaoEncontrado:
        raise HTTPException(status_code=404,
                            detail="pedido não encontrado: %s" % entrada.pedidoId) from None
    except PedidosIndisponivel as erro:
        raise HTTPException(status_code=503, detail=str(erro)) from None

    return RespostaCotacaoDePedido(
        pedidoId=resultado.pedido_id,
        modalidade=resultado.modalidade,
        valor=resultado.valor,
        prazoDias=resultado.prazo_dias,
        pesoKg=resultado.peso_kg,
        distanciaKm=resultado.distancia_km,
        cargaFechada=resultado.carga_fechada,
    )
