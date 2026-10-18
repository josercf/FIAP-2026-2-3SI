"""RESGATE do TODO-3: o Spy, resolvido.

Rede de segurança, não atalho. Leia o cabeçalho de `resgate/LEIA-ME.md`
antes de copiar qualquer coisa daqui.
"""

import pytest
from unittest.mock import Mock, call

from app.cliente_pedidos import PedidoResumo
from app.cotador import CotadorDePedido
from app.distancias import DISTANCIA_PADRAO_KM, TabelaDistancias
from conftest import PEDIDO_LEVE


class ClientePedidosStub:
    def __init__(self, pedido):
        self._pedido = pedido

    def buscar(self, pedido_id):
        return self._pedido


def test_a_tabela_e_consultada_na_ordem_do_pedido():
    """Origem primeiro, destino depois. A simetria da tabela esconde a troca.

    Este é o teste que só o Spy escreve: `km("LDB", "SAO")` devolveria
    exatamente 500,0 e nenhum número da cotação mudaria.
    """
    espia = Mock(wraps=TabelaDistancias())
    cotador = CotadorDePedido(ClientePedidosStub(PEDIDO_LEVE), tabela=espia)

    cotador.cotar("PED-1001", "expresso")

    assert espia.km.call_args_list == [call("SAO", "LDB")]


def test_o_espiao_nao_altera_o_comportamento():
    """Spy observa, não substitui: o valor é o mesmo com e sem ele.

    É isso que separa Spy de Stub. Se a cotação com o espião divergisse da
    cotação com a tabela real, o dublê teria deixado de ser observação e
    virado simulação.
    """
    cliente = ClientePedidosStub(PEDIDO_LEVE)
    com_tabela_real = CotadorDePedido(cliente, tabela=TabelaDistancias())
    com_espiao = CotadorDePedido(cliente, tabela=Mock(wraps=TabelaDistancias()))

    assert (com_espiao.cotar("PED-1001", "expresso").valor
            == pytest.approx(com_tabela_real.cotar("PED-1001", "expresso").valor))


def test_rota_fora_da_tabela_cai_na_distancia_padrao_e_ainda_assim_consulta():
    """Cliente novo não derruba a cotação: rota desconhecida vira rota média.

    O Spy prova as duas coisas ao mesmo tempo: a tabela foi consultada com o
    par certo, e o número que voltou foi o padrão de 750 km.
    """
    pedido = PedidoResumo(id="PED-2001", origem="VIX", destino="CWB",
                          peso_kg=200.0)
    espia = Mock(wraps=TabelaDistancias())
    cotador = CotadorDePedido(ClientePedidosStub(pedido), tabela=espia)

    cotacao = cotador.cotar("PED-2001", "padrao")

    espia.km.assert_called_once_with("VIX", "CWB")
    assert cotacao.distancia_km == pytest.approx(DISTANCIA_PADRAO_KM)
