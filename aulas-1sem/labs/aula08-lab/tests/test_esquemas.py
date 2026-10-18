"""Testes das lacunas TODO-1 e TODO-2: o contrato que o modelo enxerga.

Estes testes ficam vermelhos até você preencher os dois esquemas em
`agente/esquemas.py`. Isso é proposital: a suíte descreve o comportamento
esperado antes de ele existir, que é o mesmo ciclo que a Aula 10 formaliza
como TDD.
"""
import pytest

from agente import esquemas

OBRIGATORIOS_ALTERACAO = ("pedido_id", "logradouro", "numero", "cidade", "uf",
                          "cep")


@pytest.mark.parametrize("esquema,lacuna", [
    (lambda: esquemas.ESQUEMA_CONSULTAR_STATUS, "TODO-1"),
    (lambda: esquemas.ESQUEMA_ALTERAR_ENDERECO, "TODO-2"),
])
def test_esquema_foi_preenchido(esquema, lacuna):
    assert esquema(), "a lacuna %s ainda está vazia em agente/esquemas.py" % lacuna


def test_consulta_exige_o_identificador_do_pedido():
    esquema = esquemas.ESQUEMA_CONSULTAR_STATUS
    assert esquema.get("type") == "object"
    assert "pedido_id" in (esquema.get("required") or [])
    assert "pedido_id" in (esquema.get("properties") or {})


def test_consulta_fecha_a_porta_para_campo_extra():
    """`additionalProperties: false` é o que impede o modelo de contrabandear
    um campo que o Command não espera."""
    assert esquemas.ESQUEMA_CONSULTAR_STATUS.get("additionalProperties") is False


def test_alteracao_exige_os_seis_campos_do_contrato():
    requeridos = esquemas.ESQUEMA_ALTERAR_ENDERECO.get("required") or []
    for campo in OBRIGATORIOS_ALTERACAO:
        assert campo in requeridos, "falta '%s' em required" % campo


def test_complemento_e_opcional():
    """O contrato do serviço de Pedidos trata complemento como opcional;
    exigi-lo faria o agente recusar alteração legítima."""
    requeridos = esquemas.ESQUEMA_ALTERAR_ENDERECO.get("required") or []
    assert "complemento" not in requeridos


def test_todo_campo_requerido_esta_declarado_em_properties():
    for esquema in (esquemas.ESQUEMA_CONSULTAR_STATUS,
                    esquemas.ESQUEMA_ALTERAR_ENDERECO):
        propriedades = esquema.get("properties") or {}
        for campo in esquema.get("required") or []:
            assert campo in propriedades, (
                "'%s' está em required mas não em properties" % campo)


def test_as_duas_ferramentas_sao_declaradas_ao_modelo():
    nomes = [f["function"]["name"] for f in esquemas.ferramentas()]
    assert nomes == ["consultar_status_pedido", "alterar_endereco_entrega"]


def test_descricao_da_alteracao_avisa_o_modelo_sobre_o_cep():
    """A descrição é interface, não comentário: é por ela que o modelo aprende
    a pedir o CEP em vez de inventar um."""
    declaracao = esquemas.ferramentas()[1]["function"]
    assert "CEP" in declaracao["description"].upper()
