"""Configuração comum da suíte de testes do serviço de frete.

CONGELADO. Não é tarefa, mas leia: é aqui que a regra da aula vira máquina.

Um teste de unidade não toca a rede. Isso costuma ser dito e não conferido,
e o resultado é a suíte que passa na sua máquina, passa na do colega e
quebra no pipeline porque lá o serviço vizinho não estava no ar.

A `fixture` abaixo tira a dúvida: durante qualquer teste desta pasta,
`socket.connect` levanta exceção. Se o seu teste abrir conexão, ele falha na
hora, com uma mensagem que diz o que aconteceu.

Não é paranoia acadêmica, é o mesmo efeito do plugin `pytest-socket`, aqui
escrito à mão em quinze linhas para não pedir dependência nova e para que
você veja como funciona.
"""

import socket

import pytest

from app.cliente_pedidos import PedidoResumo


class RedeProibidaNoTesteDeUnidade(RuntimeError):
    """Levantada quando um teste desta pasta tenta abrir conexão."""


@pytest.fixture(autouse=True)
def sem_rede(monkeypatch):
    """Bloqueia a rede em todos os testes desta pasta.

    Se este erro aparecer para você, o diagnóstico é sempre o mesmo: em
    algum ponto o teste está usando o `ClientePedidosHttp` de verdade, em
    vez de um dublê. Troque a dependência no construtor do cotador.
    """

    def recusar(self, *args, **kwargs):
        raise RedeProibidaNoTesteDeUnidade(
            "este teste tentou abrir uma conexão de rede. Teste de unidade "
            "não fala com outro processo: use um dublê no lugar do "
            "ClientePedidosHttp.")

    monkeypatch.setattr(socket.socket, "connect", recusar)
    monkeypatch.setattr(socket.socket, "connect_ex", recusar)


# ---------------------------------------------------------------------------
# Dados de apoio, iguais aos da base congelada do serviço de Pedidos.
# ---------------------------------------------------------------------------
PEDIDO_LEVE = PedidoResumo(id="PED-1001", origem="SAO", destino="LDB",
                           peso_kg=100.0)
"""Rota de referência do laboratório: SAO -> LDB, 500 km, 100 kg."""

PEDIDO_CARGA_FECHADA = PedidoResumo(id="PED-1004", origem="CWB", destino="POA",
                                    peso_kg=780.0)
"""710 km, abaixo do peso de carga fechada. Serve de contraste."""

PEDIDO_PESADO = PedidoResumo(id="PED-1003", origem="BHZ", destino="SSA",
                             peso_kg=12500.0)
"""1370 km e 12,5 t: dispara o desconto de carga fechada e o pernoite."""

PEDIDO_ACIMA_DO_LIMITE = PedidoResumo(id="PED-9999", origem="SAO", destino="RIO",
                                      peso_kg=42000.0)
"""Acima da capacidade da frota: o cotador recusa."""


@pytest.fixture
def pedido_leve():
    """O pedido da rota de referência, pronto para o seu dublê devolver."""
    return PEDIDO_LEVE
