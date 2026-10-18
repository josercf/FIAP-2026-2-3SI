"""RESGATE do TODO-1: o Stub, resolvido.

Rede de segurança, não atalho. Leia o cabeçalho de `resgate/LEIA-ME.md`
antes de copiar qualquer coisa daqui.
"""

import pytest

from app.cotador import CargaAcimaDoLimite, CotadorDePedido
from conftest import (
    PEDIDO_ACIMA_DO_LIMITE,
    PEDIDO_LEVE,
    PEDIDO_PESADO,
)


class ClientePedidosStub:
    """Dublê que responde sempre o mesmo pedido, sem tocar em rede.

    Cinco linhas, sem herança: `ClientePedidos` é um `Protocol`, então
    basta ter o método com a assinatura certa.
    """

    def __init__(self, pedido):
        self._pedido = pedido

    def buscar(self, pedido_id):
        return self._pedido


def test_rota_de_referencia_no_expresso_sai_por_545_em_um_dia():
    """SAO -> LDB, 500 km, 100 kg: o valor de tabela, sem desconto."""
    cotador = CotadorDePedido(ClientePedidosStub(PEDIDO_LEVE))

    cotacao = cotador.cotar("PED-1001", "expresso")

    assert cotacao.valor == pytest.approx(545.00)
    assert cotacao.prazo_dias == 1
    assert cotacao.carga_fechada is False


def test_carga_fechada_recebe_o_desconto_comercial():
    """A partir de 1000 kg o cliente ocupa o veículo e paga 8 por cento menos.

    BHZ -> SSA são 1370 km, e o pedido tem 12500 kg. No padrão a tabela dá
    1370 x 0,60 + 12500 x 0,80 = 10822,00, e o desconto de carga fechada
    fecha em 9956,24.

    O número está escrito à mão de propósito. A primeira versão deste teste
    calculava o esperado com `bruto * (1 - DESCONTO_CARGA_FECHADA)`,
    importando a constante do próprio código sob teste, e passava com o
    desconto zerado: os dois lados da igualdade mudavam juntos. Teste que
    repete a fórmula da implementação não testa a fórmula, testa a si
    mesmo.
    """
    cotador = CotadorDePedido(ClientePedidosStub(PEDIDO_PESADO))

    cotacao = cotador.cotar("PED-1003", "padrao")

    assert cotacao.valor == pytest.approx(9956.24)
    assert cotacao.carga_fechada is True


def test_rota_longa_ganha_um_dia_de_pernoite():
    """Acima de 1000 km o motorista para para descanso, e o prazo cresce.

    BHZ -> SSA são 1370 km. No padrão, `ceil(1370 / 500) + 1` dá 4 dias, e
    o pernoite acrescenta o quinto.
    """
    cotador = CotadorDePedido(ClientePedidosStub(PEDIDO_PESADO))

    assert cotador.cotar("PED-1003", "padrao").prazo_dias == 5


def test_carga_acima_da_capacidade_da_frota_e_recusada():
    """42 toneladas em um pedido não é atraso: é pedido que não se aceita."""
    cotador = CotadorDePedido(ClientePedidosStub(PEDIDO_ACIMA_DO_LIMITE))

    with pytest.raises(CargaAcimaDoLimite):
        cotador.cotar("PED-9999", "expresso")


def test_pedido_leve_em_rota_curta_nao_recebe_desconto_nem_pernoite():
    """O caso de contraste: nenhuma das duas regras comerciais dispara.

    Sem este teste, um desconto aplicado a todo mundo passaria despercebido
    pelos testes de carga fechada, que só olham para o caso em que ele
    existe.
    """
    cotador = CotadorDePedido(ClientePedidosStub(PEDIDO_LEVE))

    cotacao = cotador.cotar("PED-1001", "economico")

    assert cotacao.valor == pytest.approx(265.00)
    assert cotacao.prazo_dias == 4
    assert cotacao.carga_fechada is False
