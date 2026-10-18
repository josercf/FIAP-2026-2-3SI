"""Testes das lacunas TODO-3, TODO-4 e TODO-5: a camada de comandos.

Nenhum teste aqui abre socket: o cliente do serviço de Pedidos é substituído
pelo dublê `ApiFalsa` do `conftest.py`. É isso que torna estes testes de
unidade, e não de integração, e o que permite provar o essencial da lacuna
TODO-5: que, na recusa, **nenhuma** chamada chegou à API.
"""
import pytest

from agente import auditoria
from agente.comandos import (AlterarEnderecoEntrega, ConsultarStatusPedido,
                             Despachante)

ENDERECO_COMPLETO = {
    "pedido_id": "PED-1042",
    "logradouro": "Avenida Paulista",
    "numero": "1106",
    "cidade": "São Paulo",
    "uf": "SP",
    "cep": "01311-000",
}


def endereco_sem_cep():
    argumentos = dict(ENDERECO_COMPLETO)
    argumentos.pop("cep")
    return argumentos


# ---------------------------------------------------------------------------
# TODO-3
# ---------------------------------------------------------------------------
def test_consultar_status_chama_a_rota_do_contrato(api):
    resultado = ConsultarStatusPedido().executar({"pedido_id": "PED-1042"})
    assert api.chamadas == [("obter_status", "PED-1042", None)]
    assert resultado["status"] == "EM_TRANSITO"


def test_consulta_autorizada_entra_na_trilha(api, trilha):
    resultado = Despachante(caminho_auditoria=trilha).despachar(
        "consultar_status_pedido", {"pedido_id": "PED-1042"})
    assert resultado.autorizado
    assert auditoria.contar(trilha)[auditoria.AUTORIZADO] == 1


# ---------------------------------------------------------------------------
# TODO-4
# ---------------------------------------------------------------------------
def test_alterar_endereco_monta_o_corpo_do_patch(api):
    AlterarEnderecoEntrega().executar(dict(ENDERECO_COMPLETO))
    acao, pedido_id, corpo = api.chamadas[0]
    assert acao == "alterar_endereco"
    assert pedido_id == "PED-1042"
    assert corpo["cep"] == "01311-000"


def test_pedido_id_vai_na_url_e_nao_no_corpo(api):
    AlterarEnderecoEntrega().executar(dict(ENDERECO_COMPLETO))
    _, _, corpo = api.chamadas[0]
    assert "pedido_id" not in corpo


def test_complemento_ausente_nao_e_inventado(api):
    AlterarEnderecoEntrega().executar(dict(ENDERECO_COMPLETO))
    _, _, corpo = api.chamadas[0]
    assert "complemento" not in corpo


def test_alteracao_autorizada_entra_na_trilha(api, trilha):
    resultado = Despachante(caminho_auditoria=trilha).despachar(
        "alterar_endereco_entrega", dict(ENDERECO_COMPLETO))
    assert resultado.autorizado
    assert auditoria.contar(trilha)[auditoria.AUTORIZADO] == 1


# ---------------------------------------------------------------------------
# TODO-5: o critério que separa integração de engenharia
# ---------------------------------------------------------------------------
def test_alteracao_sem_cep_e_recusada(api, trilha):
    resultado = Despachante(caminho_auditoria=trilha).despachar(
        "alterar_endereco_entrega", endereco_sem_cep())
    assert resultado.veredito == auditoria.RECUSADO


def test_alteracao_sem_cep_nao_chega_a_api(api, trilha):
    """O ponto da aula inteira: a chamada malformada não sai do agente."""
    Despachante(caminho_auditoria=trilha).despachar(
        "alterar_endereco_entrega", endereco_sem_cep())
    assert api.chamadas == []


def test_recusa_registra_o_motivo_com_o_campo_que_faltou(api, trilha):
    resultado = Despachante(caminho_auditoria=trilha).despachar(
        "alterar_endereco_entrega", endereco_sem_cep())
    assert "cep" in resultado.motivo.lower()
    assert auditoria.contar(trilha)[auditoria.RECUSADO] == 1


def test_recusa_devolve_ao_modelo_o_que_faltou(api, trilha):
    """A recusa volta para a conversa: é assim que o agente consegue pedir o
    CEP ao cliente em vez de simplesmente travar."""
    resultado = Despachante(caminho_auditoria=trilha).despachar(
        "alterar_endereco_entrega", endereco_sem_cep())
    assert "cep" in str(resultado.conteudo).lower()


def test_ferramenta_inexistente_e_recusada_e_auditada(api, trilha):
    resultado = Despachante(caminho_auditoria=trilha).despachar(
        "cancelar_pedido", {"pedido_id": "PED-1042"})
    assert resultado.veredito == auditoria.RECUSADO
    assert api.chamadas == []
    assert auditoria.contar(trilha)[auditoria.RECUSADO] == 1


def test_erro_do_servico_vira_falhou_e_nao_recusado(api, trilha):
    """`RECUSADO` e `FALHOU` são coisas diferentes: uma é decisão do agente, a
    outra é resposta do sistema. Misturar os dois cega a auditoria."""
    argumentos = dict(ENDERECO_COMPLETO, pedido_id="PED-9999")
    resultado = Despachante(caminho_auditoria=trilha).despachar(
        "consultar_status_pedido", {"pedido_id": "PED-9999"})
    assert resultado.veredito == auditoria.FALHOU
    assert auditoria.contar(trilha)[auditoria.FALHOU] == 1
    assert argumentos["pedido_id"] == "PED-9999"


# ---------------------------------------------------------------------------
# O Despachante como invoker: aberto para comandos novos
# ---------------------------------------------------------------------------
def test_despachante_aceita_comando_novo_sem_ser_alterado(trilha):
    """Prova de que o invoker é fechado para modificação: um comando novo
    entra por composição, não por edição do Despachante."""

    class Comando:
        nome = "listar_frota"
        esquema = {"type": "object", "properties": {}, "required": []}

        def validar(self, argumentos):
            return []

        def executar(self, argumentos):
            return {"caminhoes": 400}

    despachante = Despachante(comandos=[Comando()], caminho_auditoria=trilha)
    resultado = despachante.despachar("listar_frota", {})
    assert resultado.autorizado
    assert resultado.conteudo == {"caminhoes": 400}


@pytest.mark.parametrize("nome", ["consultar_status_pedido",
                                  "alterar_endereco_entrega"])
def test_nomes_dos_comandos_batem_com_os_declarados_ao_modelo(nome):
    """Nome divergente entre o esquema e o Command produz recusa por
    'ferramenta não existe', que é um bug difícil de enxergar em produção."""
    assert nome in Despachante().comandos
