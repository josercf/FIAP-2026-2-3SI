"""
LogiTech Enterprise - Cálculo de Frete (apoio ao Bounded Context de Pedidos).

ATENÇÃO, LEIA ANTES DE COMPARAR COM A AULA 06
---------------------------------------------
Versão **mínima**, escrita para o laboratório da Aula 07 ter o que
orquestrar. Cumpre o contrato da plataforma (ADR-006): porta 8000, as duas
rotas e `/health` devolvendo {"status": "ok"}.

O que ela **não** é: a implementação da Aula 06. Lá o serviço nasce com
`EstrategiaFrete` como protocolo comum, `FreteExpresso` e `FreteEconomico`
como estratégias e um registro que permite acrescentar modalidade sem tocar
na rota, que é o conteúdo daquela aula. Aqui há uma tabela de modalidades e
uma fórmula, porque o assunto de hoje é orquestração.

Não é tarefa. Não editem este arquivo.

Rotas (ADR-006 e ADR-009):
    GET  /health                    aberta, sempre
    POST /api/v1/frete/cotacao      qualquer papel autenticado
         entra {origem, destino, pesoKg, modalidade}
         sai   {valor, prazoDias, modalidade}

Versão da Aula 16: ganhou CORS (ADR-008) e validação de JWT (ADR-009), as duas
governadas por variável de ambiente. Com `LOGITECH_AUTH_ATIVA=false` este
serviço se comporta exatamente como na Aula 07.
"""

import os
import time
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import seguranca

INICIADO_EM = time.time()

# Tabela de modalidades: preço por quilo, taxa fixa e prazo em dias.
# Na Aula 06 cada linha desta tabela vira uma classe de estratégia.
MODALIDADES = {
    "economico": {"por_kg": 1.80, "taxa": 12.00, "prazo_dias": 7},
    "expresso": {"por_kg": 4.20, "taxa": 29.90, "prazo_dias": 2},
    "refrigerado": {"por_kg": 6.50, "taxa": 48.00, "prazo_dias": 3},
}

app = FastAPI(
    title="LogiTech - Cálculo de Frete",
    version="1.0.0",
    description="Serviço de cotação de frete da plataforma LogiTech Enterprise.",
)

# CORS entrou no contrato na ADR-008, quando o consumidor deixou de ser outro
# servidor e passou a ser o navegador. `curl` ignora CORS: sem esta linha a
# suíte fica verde e a tela do Portal fica vazia.
app.add_middleware(
    CORSMiddleware,
    allow_origins=seguranca.origens_cors(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def autenticado(authorization: str = Header(default=None)):
    """Qualquer papel serve nesta rota, mas alguém precisa estar autenticado."""
    if not seguranca.ativa():
        return {"sub": "anonimo", "realm_access": {"roles": []}}
    try:
        return seguranca.exigir(authorization)
    except seguranca.ErroDePapel as erro:
        raise HTTPException(status_code=403, detail=str(erro))
    except seguranca.ErroDeToken as erro:
        raise HTTPException(status_code=401, detail=str(erro))


class PedidoDeCotacao(BaseModel):
    origem: str = Field(min_length=2, description="Cidade ou CEP de coleta")
    destino: str = Field(min_length=2, description="Cidade ou CEP de entrega")
    pesoKg: float = Field(gt=0, le=30000, description="Peso da carga em quilos")
    modalidade: Literal["economico", "expresso", "refrigerado"] = "economico"


class Cotacao(BaseModel):
    valor: float
    prazoDias: int
    modalidade: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "servico": "frete",
        "uptime_s": int(time.time() - INICIADO_EM),
        "modalidades": sorted(MODALIDADES),
        "auth_ativa": seguranca.ativa(),
    }


@app.post("/api/v1/frete/cotacao", response_model=Cotacao)
def cotar(pedido: PedidoDeCotacao, quem: dict = Depends(autenticado)) -> Cotacao:
    """Cota o frete de uma carga.

    Fórmula deliberadamente simples e determinística: o mesmo pedido devolve
    sempre o mesmo valor. Isso é o que permite ao verificador do laboratório
    conferir a jornada de um pedido pela plataforma sem depender de sorte.
    """
    regra = MODALIDADES[pedido.modalidade]
    valor = round(regra["taxa"] + regra["por_kg"] * pedido.pesoKg, 2)
    return Cotacao(valor=valor, prazoDias=regra["prazo_dias"], modalidade=pedido.modalidade)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("LOGITECH_PORTA", "8000")),
        log_level="warning",
    )
