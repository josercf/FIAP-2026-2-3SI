"""Contrato HTTP do serviço de frete, descrito com Pydantic.

CONGELADO. Não é tarefa da Aula 10.

Os nomes dos campos são os da ADR-006 e **não** se traduzem: entra
`{origem, destino, pesoKg, modalidade}`, sai `{valor, prazoDias, modalidade}`.
É esse contrato que o Portal do Cliente consome hoje, em TypeScript, com os
mesmos nomes de campo do outro lado da rede.
"""

from pydantic import BaseModel, Field


class PedidoCotacao(BaseModel):
    """O que o cliente da API envia para pedir uma cotação avulsa."""

    origem: str = Field(min_length=3, max_length=3,
                        description="Código do centro de distribuição de origem, por exemplo SAO")
    destino: str = Field(min_length=3, max_length=3,
                         description="Código do centro de distribuição de destino, por exemplo LDB")
    pesoKg: float = Field(gt=0, le=30000,
                          description="Peso da carga em quilogramas")
    modalidade: str = Field(min_length=3, max_length=40,
                            description="Nome da modalidade de frete registrada")


class RespostaCotacao(BaseModel):
    """O que o serviço devolve. Valor em reais, prazo em dias corridos."""

    valor: float
    prazoDias: int
    modalidade: str


class CotacaoDePedidoPedida(BaseModel):
    """Entrada da recotação de um pedido que já existe na LogiTech."""

    pedidoId: str = Field(min_length=8, max_length=8,
                          description="Identificador no formato PED-0000")
    modalidade: str = Field(min_length=3, max_length=40)


class RespostaCotacaoDePedido(BaseModel):
    """Saída da recotação, com os dados que sustentam o número."""

    pedidoId: str
    modalidade: str
    valor: float
    prazoDias: int
    pesoKg: float
    distanciaKm: float
    cargaFechada: bool


class RespostaSaude(BaseModel):
    """Corpo de `GET /health`, o mesmo em todos os serviços da plataforma."""

    status: str = "ok"
