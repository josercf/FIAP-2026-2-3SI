"""API HTTP do serviço de frete da LogiTech (FastAPI, porta 8000).

Este arquivo é o **antes** da aula: a rota conhece cada modalidade pelo nome
e escolhe a fórmula numa cadeia de `if`. Funciona, responde certo, e mesmo
assim é o problema: cada campanha comercial nova obriga a abrir esta função
e acrescentar um ramo, com risco de quebrar os que já estavam ali.

A lacuna TODO-3 termina aqui: quando o registro de estratégias estiver
preenchido, esta rota deixa de citar modalidade nenhuma. O `verificar.py`
confere exatamente isso, procurando nome de modalidade no texto deste
arquivo.

Para subir:

    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

Documentação OpenAPI gerada pelo Pydantic: http://localhost:8000/docs
"""

from math import ceil

from fastapi import FastAPI, HTTPException

from .distancias import distancia_km
from .modelos import PedidoCotacao, RespostaCotacao, RespostaSaude
from .registro import modalidades

app = FastAPI(
    title="LogiTech Frete",
    version="1.0.0",
    description="Motor de cálculo de frete da LogiTech Enterprise AI Platform.",
)


@app.get("/health", response_model=RespostaSaude, tags=["infraestrutura"])
def saude() -> RespostaSaude:
    """Sonda de saúde exigida pela ADR-006.

    A Aula 07 apoia o `healthcheck` do Docker Compose nesta rota: ela
    precisa responder `200` e `{"status": "ok"}` sem depender de banco,
    de rede externa nem de nada que possa estar fora do ar.
    """
    return RespostaSaude(status="ok")


@app.get("/api/v1/frete/modalidades", tags=["frete"])
def listar_modalidades() -> dict[str, list[str]]:
    """As modalidades que o registro conhece.

    Repare que esta rota já está pronta e já é fechada para modificação:
    ela pergunta ao registro. Depois do TODO-3, a rota de cotação fica
    exatamente assim.
    """
    return {"modalidades": modalidades()}


@app.post("/api/v1/frete/cotacao", response_model=RespostaCotacao, tags=["frete"])
def cotar(pedido: PedidoCotacao) -> RespostaCotacao:
    """Calcula o frete de uma carga entre dois centros de distribuição.

    TODO-3: troque a cadeia de `if` abaixo por duas linhas que consultam o
    registro (`obter(pedido.modalidade)`) e executam a estratégia devolvida.
    Depois disso, nenhum nome de modalidade pode sobrar neste arquivo.
    """
    distancia = distancia_km(pedido.origem, pedido.destino)

    # TODO-3: este bloco inteiro sai daqui.
    if pedido.modalidade == "expresso":
        valor = round(distancia * 0.85 + pedido.pesoKg * 1.20, 2)
        prazo = max(1, ceil(distancia / 700))
    elif pedido.modalidade == "economico":
        valor = round(distancia * 0.42 + pedido.pesoKg * 0.55, 2)
        prazo = ceil(distancia / 350) + 2
    elif pedido.modalidade == "padrao":
        valor = round(distancia * 0.60 + pedido.pesoKg * 0.80, 2)
        prazo = ceil(distancia / 500) + 1
    else:
        raise HTTPException(
            status_code=422,
            detail="modalidade não suportada: %s" % pedido.modalidade)

    return RespostaCotacao(valor=valor, prazoDias=prazo,
                           modalidade=pedido.modalidade)
