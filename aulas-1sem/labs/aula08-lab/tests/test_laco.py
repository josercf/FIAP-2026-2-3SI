"""Testes do laço de conversa e da trilha de auditoria.

O laço já vem pronto, e estes testes passam desde o primeiro minuto: eles
documentam o contrato entre o laço e a camada de comandos, e quebram se
alguém mudar o formato dos argumentos ou o limite de rodadas.
"""
from agente import auditoria, laco, llm
from agente.comandos import Despachante


class DespachanteEspiao:
    """Registra o que foi despachado, sem executar nada."""

    def __init__(self, veredito=auditoria.AUTORIZADO):
        self.recebidos = []
        self.veredito = veredito

    def despachar(self, nome, argumentos):
        from agente.comandos import Resultado
        self.recebidos.append((nome, argumentos))
        return Resultado(self.veredito, {"ok": True}, "motivo de teste")


class ClienteMudo:
    """Devolve sempre a mesma intenção de chamada: serve para provar que o
    laço não gira para sempre."""

    def conversar(self, mensagens, ferramentas):
        return {"role": "assistant", "content": "",
                "tool_calls": [{"function": {"name": "consultar_status_pedido",
                                             "arguments": {"pedido_id": "PED-1042"}}}]}


def test_argumentos_em_dicionario_sao_aceitos():
    assert laco._argumentos({"pedido_id": "PED-1042"}) == {"pedido_id": "PED-1042"}


def test_argumentos_em_string_json_sao_aceitos():
    """A API compatível com OpenAI entrega os argumentos como string."""
    assert laco._argumentos('{"pedido_id": "PED-1042"}') == {"pedido_id": "PED-1042"}


def test_argumentos_invalidos_viram_dicionario_vazio():
    """Argumento ilegível não é adivinhado: vira vazio e a validação recusa."""
    assert laco._argumentos("{isto não é json") == {}


def test_laco_para_no_limite_de_rodadas():
    espiao = DespachanteEspiao()
    resposta, eventos = laco.conversar("Onde está o PED-1042?", ClienteMudo(),
                                        espiao, max_rodadas=3)
    assert len(eventos) == 3
    assert "limite" in resposta.lower()


def test_roteiro_simulado_de_status_chama_a_ferramenta_certa():
    espiao = DespachanteEspiao()
    cliente = llm.ClienteSimulado(roteiro="status")
    resposta, eventos = laco.conversar("Onde está o PED-1042?", cliente, espiao)
    assert espiao.recebidos[0][0] == "consultar_status_pedido"
    assert "PED-1042" in resposta


def test_roteiro_simulado_de_recusa_tenta_sem_cep_primeiro():
    """O roteiro da recusa existe para exercitar TODO-5 sem depender do
    modelo: a primeira intenção vem incompleta de propósito."""
    espiao = DespachanteEspiao(veredito=auditoria.RECUSADO)
    cliente = llm.ClienteSimulado(roteiro="recusa")
    laco.conversar("Mudar o endereço do PED-1043", cliente, espiao)
    _, primeiros_argumentos = espiao.recebidos[0]
    assert "cep" not in primeiros_argumentos
    _, segundos_argumentos = espiao.recebidos[1]
    assert segundos_argumentos["cep"] == "01415-000"


def test_escolha_de_roteiro_por_palavra_chave():
    assert llm.escolher_roteiro("Onde está o meu pedido?") == "status"
    assert llm.escolher_roteiro("Quero mudar o endereço de entrega") == "recusa"
    assert llm.escolher_roteiro(
        "Mudar endereço para Rua Bela Cintra 495, CEP 01415-000") == "endereco"


def test_trilha_de_auditoria_e_acrescentada_e_nao_reescrita(trilha):
    auditoria.registrar("consultar_status_pedido", auditoria.AUTORIZADO,
                        {"pedido_id": "PED-1042"}, {"status": "EM_TRANSITO"},
                        caminho=trilha)
    auditoria.registrar("alterar_endereco_entrega", auditoria.RECUSADO,
                        {"pedido_id": "PED-1043"}, "falta o campo 'cep'",
                        caminho=trilha)
    contagem = auditoria.contar(trilha)
    assert contagem[auditoria.AUTORIZADO] == 1
    assert contagem[auditoria.RECUSADO] == 1


def test_barra_vertical_no_argumento_nao_quebra_a_tabela(trilha):
    auditoria.registrar("alterar_endereco_entrega", auditoria.AUTORIZADO,
                        {"logradouro": "Rua A | fundos"}, {"ok": True},
                        caminho=trilha)
    assert auditoria.contar(trilha)[auditoria.AUTORIZADO] == 1


def test_despachante_real_usa_a_trilha_indicada(api, trilha):
    """O caminho da trilha é injetável de propósito: o verificador e os testes
    não podem escrever na trilha que o aluno entrega."""
    Despachante(caminho_auditoria=trilha).despachar(
        "consultar_status_pedido", {"pedido_id": "PED-1042"})
    with open(trilha, encoding="utf-8") as f:
        assert "consultar_status_pedido" in f.read()
