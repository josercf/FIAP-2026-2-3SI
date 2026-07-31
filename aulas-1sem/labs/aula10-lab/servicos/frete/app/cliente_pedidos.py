"""A fronteira do serviço de frete com o serviço de Pedidos.

CONGELADO. Não é tarefa da Aula 10.

Este é o arquivo que dá sentido ao laboratório de hoje. O frete precisa
saber o **peso** da carga para cotar, e o peso não é dado dele: é dado do
serviço de Pedidos, que roda em outro processo, em outra porta, e na Aula 07
em outro container.

Consequência direta: um teste de unidade do cálculo de frete **não pode**
depender de `pedidos` estar no ar. Se depender, ele deixa de ser teste de
unidade e vira teste de integração disfarçado, com três defeitos que se
pagam todo dia:

1. fica lento, porque abre conexão de rede;
2. fica intermitente, porque falha quando o outro serviço cai, quando a
   máquina está sem rede ou quando o colega ao lado subiu o serviço na mesma
   porta;
3. fica mentiroso, porque quando ele quebra ninguém sabe se o defeito é do
   cálculo de frete ou do serviço de Pedidos.

A saída é a separação abaixo: `ClientePedidos` é um **contrato** (um
`Protocol`), e `ClientePedidosHttp` é a implementação que fala HTTP de
verdade. Quem calcula frete depende do contrato, não da implementação. No
teste, entra um dublê no lugar; em produção, entra o HTTP.

Repare que `ClientePedidosHttp` não tem regra de negócio nenhuma: ele só
traduz JSON em objeto. Isso é proposital. Fronteira burra é fronteira fácil
de dublar, e o que sobra do outro lado é regra pura, que se testa rápido.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

PEDIDOS_URL_PADRAO = "http://localhost:8080"


@dataclass(frozen=True)
class PedidoResumo:
    """O recorte do pedido que o frete precisa conhecer.

    Não é o pedido inteiro de propósito: o serviço de frete não tem nada que
    saber o nome do cliente nem o histórico de status. Trazer só o
    necessário mantém o acoplamento entre os dois contextos no mínimo.
    """

    id: str
    origem: str
    destino: str
    peso_kg: float


class PedidoNaoEncontrado(Exception):
    """O serviço de Pedidos respondeu 404 para este identificador."""


class PedidosIndisponivel(Exception):
    """O serviço de Pedidos não respondeu, ou respondeu erro de servidor."""


@runtime_checkable
class ClientePedidos(Protocol):
    """Contrato de quem sabe buscar um pedido, seja lá como.

    Um `Protocol` do módulo `typing` descreve o formato esperado sem obrigar
    herança: qualquer objeto com um método `buscar` desta assinatura já é um
    `ClientePedidos`. É por isso que o dublê do seu teste não precisa herdar
    de nada.
    """

    def buscar(self, pedido_id: str) -> PedidoResumo:
        """Devolve o resumo do pedido ou levanta `PedidoNaoEncontrado`."""
        ...


class ClientePedidosHttp:
    """Implementação real: fala HTTP com o serviço de Pedidos.

    Endereço nunca cravado no código, como manda a ADR-006: vem de
    `LOGITECH_PEDIDOS_URL`, com padrão de desenvolvimento local.

    Esta classe **não** aparece em nenhum teste de unidade do laboratório. É
    exatamente esse o ponto: ela é a única parte que precisa de rede, está
    isolada em nove linhas, e tudo o que fica atrás dela se testa sem rede.
    """

    def __init__(self, base_url: str | None = None, timeout_s: float = 3.0) -> None:
        self._base_url = (base_url
                          or os.getenv("LOGITECH_PEDIDOS_URL", PEDIDOS_URL_PADRAO)
                          ).rstrip("/")
        self._timeout_s = timeout_s

    def buscar(self, pedido_id: str) -> PedidoResumo:
        import httpx  # importado aqui para o módulo carregar sem a dependência

        url = "%s/api/v1/pedidos/%s" % (self._base_url, pedido_id)
        try:
            resposta = httpx.get(url, timeout=self._timeout_s)
        except httpx.HTTPError as erro:
            raise PedidosIndisponivel(
                "serviço de Pedidos não respondeu em %s: %s" % (url, erro)) from erro

        if resposta.status_code == 404:
            raise PedidoNaoEncontrado(pedido_id)
        if resposta.status_code >= 500:
            raise PedidosIndisponivel(
                "serviço de Pedidos devolveu %d" % resposta.status_code)

        dados = resposta.json()
        return PedidoResumo(
            id=dados["id"],
            origem=dados["origem"],
            destino=dados["destino"],
            peso_kg=float(dados["pesoKg"]),
        )
