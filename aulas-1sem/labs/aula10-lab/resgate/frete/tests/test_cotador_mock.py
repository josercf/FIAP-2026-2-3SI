"""RESGATE do TODO-2: o Mock, resolvido.

Rede de segurança, não atalho. Leia o cabeçalho de `resgate/LEIA-ME.md`
antes de copiar qualquer coisa daqui.
"""

import pytest
from unittest.mock import Mock

from app.cliente_pedidos import ClientePedidos
from app.cotador import CotadorDePedido, PedidoInvalido
from conftest import PEDIDO_LEVE


def cliente_mockado():
    """Um `Mock` preso ao contrato `ClientePedidos`.

    `spec=` é o que impede o teste de passar contra um método que não
    existe. Sem ele, `cliente.busca_r(...)` seria aceito de bom grado.
    """
    cliente = Mock(spec=ClientePedidos)
    cliente.buscar.return_value = PEDIDO_LEVE
    return cliente


def test_tres_modalidades_do_mesmo_pedido_batem_uma_vez_no_servico_vizinho():
    """A memória do cotador é regra de negócio, e só o Mock a enxerga.

    Os três valores devolvidos são idênticos com ou sem memória. O que muda
    é a conta de rede: três chamadas para montar uma tela só.
    """
    cliente = cliente_mockado()
    cotador = CotadorDePedido(cliente)

    for modalidade in ("expresso", "economico", "padrao"):
        cotador.cotar("PED-1001", modalidade)

    cliente.buscar.assert_called_once_with("PED-1001")


def test_identificador_invalido_nao_chega_ao_servico_de_pedidos():
    """Fail fast: chamada de rede que se sabe inútil não se faz."""
    cliente = cliente_mockado()
    cotador = CotadorDePedido(cliente)

    with pytest.raises(PedidoInvalido):
        cotador.cotar("1001", "expresso")

    cliente.buscar.assert_not_called()


def test_o_identificador_chega_normalizado_em_maiusculas():
    """O cliente digita `ped-1001` e o serviço vizinho recebe `PED-1001`.

    Sem esta asserção, a normalização poderia sumir sem que nenhum número
    mudasse: o Stub responde o mesmo pedido de qualquer jeito.
    """
    cliente = cliente_mockado()
    cotador = CotadorDePedido(cliente)

    cotador.cotar("  ped-1001 ", "padrao")

    cliente.buscar.assert_called_once_with("PED-1001")


def test_pedidos_diferentes_produzem_chamadas_diferentes():
    """A memória é por pedido, não um cache global que serve tudo igual."""
    cliente = cliente_mockado()
    cotador = CotadorDePedido(cliente)

    cotador.cotar("PED-1001", "padrao")
    cotador.cotar("PED-1002", "padrao")

    assert cliente.buscar.call_count == 2
