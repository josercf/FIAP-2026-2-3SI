"""Testes do validador de JSON Schema.

Este módulo já vem pronto no laboratório, e estes testes já passam desde o
primeiro minuto. Eles existem por dois motivos: documentam o que a validação
garante, e protegem quem resolver mexer no validador para "fazer passar".
"""
from agente import validacao

ESQUEMA = {
    "type": "object",
    "properties": {
        "pedido_id": {"type": "string", "pattern": "^PED-[0-9]{4}$"},
        "uf": {"type": "string", "pattern": "^[A-Z]{2}$"},
        "peso_kg": {"type": "number", "minimum": 0},
    },
    "required": ["pedido_id"],
    "additionalProperties": False,
}


def test_argumentos_completos_nao_geram_erro():
    assert validacao.validar({"pedido_id": "PED-1042"}, ESQUEMA) == []


def test_campo_obrigatorio_ausente_e_apontado_pelo_nome():
    erros = validacao.validar({"uf": "SP"}, ESQUEMA)
    assert any("pedido_id" in e for e in erros)


def test_campo_obrigatorio_vazio_tambem_reprova():
    erros = validacao.validar({"pedido_id": "   "}, ESQUEMA)
    assert any("pedido_id" in e for e in erros)


def test_formato_errado_reprova_pelo_pattern():
    erros = validacao.validar({"pedido_id": "1042"}, ESQUEMA)
    assert any("formato" in e for e in erros)


def test_tipo_errado_reprova():
    erros = validacao.validar({"pedido_id": 1042}, ESQUEMA)
    assert any("tipo" in e for e in erros)


def test_campo_fora_do_contrato_reprova_com_additional_properties_false():
    erros = validacao.validar(
        {"pedido_id": "PED-1042", "excluir_pedido": True}, ESQUEMA)
    assert any("excluir_pedido" in e for e in erros)


def test_esquema_vazio_reprova_apontando_a_lacuna():
    """Enquanto TODO-1 e TODO-2 não estiverem preenchidos, toda chamada é
    recusada, e a mensagem precisa dizer por quê."""
    erros = validacao.validar({"pedido_id": "PED-1042"}, {})
    assert len(erros) == 1
    assert "esquemas.py" in erros[0]


def test_booleano_nao_conta_como_numero():
    erros = validacao.validar({"pedido_id": "PED-1042", "peso_kg": True},
                              ESQUEMA)
    assert any("peso_kg" in e for e in erros)
