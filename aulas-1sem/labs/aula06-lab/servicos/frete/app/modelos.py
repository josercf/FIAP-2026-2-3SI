"""Contrato HTTP do serviço de frete, descrito com Pydantic.

Os nomes dos campos são os da ADR-006 e **não** se traduzem: entra
`{origem, destino, pesoKg, modalidade}`, sai `{valor, prazoDias, modalidade}`.
É o contrato que a Aula 07 vai orquestrar e que a Aula 08 vai consumir.

Escrever o contrato como classe Pydantic dá três coisas de uma vez: a
validação de entrada, a serialização de saída e o `/docs` do FastAPI, que é
a especificação OpenAPI gerada sem ninguém escrever YAML à mão.

Este arquivo não é tarefa: está aqui para vocês lerem o contrato.
"""

from pydantic import BaseModel, Field


class PedidoCotacao(BaseModel):
    """O que o cliente da API envia para pedir uma cotação."""

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


class RespostaSaude(BaseModel):
    """Corpo de `GET /health`, o mesmo em todos os serviços da plataforma."""

    status: str = "ok"
