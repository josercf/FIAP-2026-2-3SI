"""LogiTech Enterprise - Serviço de Pedidos (Bounded Context: Pedidos).

ATENÇÃO, LEIA ANTES DE COMPARAR COM A AULA 05
---------------------------------------------
Esta é uma versão **mínima** do serviço, escrita para o laboratório da
Aula 10 ter o que consumir. Ela cumpre o contrato da plataforma (ADR-006):
porta 8080, as rotas de leitura e `/health` devolvendo {"status": "ok"}.

O que ela **não** é: a implementação da Aula 05. Lá o serviço nasce em
Java 21 com Spring Boot 3, Repository, Factory Method e injeção de
dependência, que é o conteúdo daquela aula. Aqui há um FastAPI com os
pedidos em memória, porque o assunto de hoje é teste de unidade e React,
não arquitetura interna de serviço, e porque exigir uma JDK dentro de um
devcontainer de Python e Node custaria minutos do bloco prático sem
ensinar nada.

Diferença declarada em relação ao que você entregou na Aula 06: este
serviço já sobe com **CORS ligado**, lendo `LOGITECH_CORS_ORIGINS`. A
decisão está na ADR-008: a partir de hoje quem chama a API é o navegador,
e o navegador aplica a política de mesma origem.

Não é tarefa. Não editem este arquivo.

Rotas (ADR-006):
    GET  /health
    GET  /api/v1/pedidos
    GET  /api/v1/pedidos/{id}
    GET  /api/v1/pedidos/{id}/status

Para subir:
    cd servicos/pedidos && uvicorn app:app --port 8080 --reload
"""

import os
from datetime import date

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

CORS_PADRAO = "http://localhost:5173,http://localhost:4200"


class Pedido(BaseModel):
    """Um pedido da LogiTech, no vocabulário fixado na Aula 01.

    `pesoKg`, `origem` e `destino` são os campos que o serviço de frete
    precisa para cotar. Eles moram aqui, e não no frete: é o dono do dado
    quem responde por ele, e é por isso que o cotador da Aula 10 tem que
    fazer uma chamada de rede para saber o peso.
    """

    id: str
    cliente: str
    origem: str
    destino: str
    pesoKg: float
    status: str
    atualizadoEm: str


# Base congelada. Os identificadores e os pesos são usados pelas evidências
# do laboratório e pelo verificador: não altere estes números.
PEDIDOS = {
    "PED-1001": Pedido(id="PED-1001", cliente="Supermercados Aurora",
                       origem="SAO", destino="LDB", pesoKg=100.0,
                       status="EM_TRANSITO", atualizadoEm="2026-10-06T14:20:00"),
    "PED-1002": Pedido(id="PED-1002", cliente="Farmácias Vida",
                       origem="SAO", destino="RIO", pesoKg=42.5,
                       status="COLETADO", atualizadoEm="2026-10-06T09:05:00"),
    "PED-1003": Pedido(id="PED-1003", cliente="Metalúrgica Ipiranga",
                       origem="BHZ", destino="SSA", pesoKg=12500.0,
                       status="AGUARDANDO_COLETA", atualizadoEm="2026-10-05T18:41:00"),
    "PED-1004": Pedido(id="PED-1004", cliente="Distribuidora Pampa",
                       origem="CWB", destino="POA", pesoKg=780.0,
                       status="ENTREGUE", atualizadoEm="2026-10-04T11:12:00"),
}

app = FastAPI(
    title="LogiTech Pedidos",
    version="1.0.0",
    description="Versão mínima do serviço de Pedidos, congelada para a Aula 10.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in
                   os.getenv("LOGITECH_CORS_ORIGINS", CORS_PADRAO).split(",")
                   if o.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/health", tags=["infraestrutura"])
def saude() -> dict[str, str]:
    """Sonda de saúde exigida pela ADR-006."""
    return {"status": "ok"}


@app.get("/api/v1/pedidos", tags=["pedidos"])
def listar() -> dict[str, list[Pedido]]:
    """Todos os pedidos da base congelada, em ordem de identificador."""
    return {"pedidos": [PEDIDOS[k] for k in sorted(PEDIDOS)]}


@app.get("/api/v1/pedidos/{pedido_id}", tags=["pedidos"])
def obter(pedido_id: str) -> Pedido:
    """Um pedido pelo identificador. `404` quando não existe.

    É esta rota que o `ClientePedidosHttp` do serviço de frete chama, e é
    ela que os seus testes de unidade **não** podem depender de encontrar
    no ar.
    """
    pedido = PEDIDOS.get(pedido_id.upper())
    if pedido is None:
        raise HTTPException(status_code=404,
                            detail="pedido não encontrado: %s" % pedido_id)
    return pedido


@app.get("/api/v1/pedidos/{pedido_id}/status", tags=["pedidos"])
def status(pedido_id: str) -> dict[str, str]:
    """Situação atual do pedido, a rota que o agente da Aula 08 usa."""
    pedido = obter(pedido_id)
    return {"id": pedido.id, "status": pedido.status,
            "atualizadoEm": pedido.atualizadoEm,
            "consultadoEm": date.today().isoformat()}
