"""Testes do próprio verificador.

Verificador que erra é pior do que verificador que não existe: ele reprova
quem acertou e aprova quem não fez. Estes testes cobrem as funções de
leitura de marcador e de saída de suíte, que são onde o `verificar.py` mais
tem chance de se enganar sozinho.

Não é tarefa do laboratório, mas vale a leitura: é um exemplo pequeno de
teste de unidade sobre código que só manipula texto.
"""

import verificar


def test_normalizar_ignora_espaco_a_direita_e_fim_de_linha():
    assert verificar.normalizar("a  \r\nb\t\n") == verificar.normalizar("a\nb")


def test_impressao_digital_muda_quando_o_conteudo_muda():
    assert verificar.impressao_digital("a\nb") == verificar.impressao_digital("a  \nb")
    assert verificar.impressao_digital("a\nb") != verificar.impressao_digital("a\nc")


def test_valor_do_marcador_recusa_o_esqueleto():
    texto = "MODALIDADE_NOVA: PREENCHER\nOUTRO: refrigerado\n"
    assert verificar.valor_do_marcador("MODALIDADE_NOVA", texto) is None
    assert verificar.valor_do_marcador("OUTRO", texto) == "refrigerado"


def test_valor_do_marcador_devolve_none_quando_ausente():
    assert verificar.valor_do_marcador("NAO_EXISTE", "nada aqui") is None


def test_numero_do_marcador_aceita_virgula_e_unidade():
    texto = "VALOR_EXPRESSO_500KM: R$ 545,00\nPRAZO_EXPRESSO_500KM: 1 dia\n"
    assert verificar.numero_do_marcador("VALOR_EXPRESSO_500KM", texto) == 545.0
    assert verificar.numero_do_marcador("PRAZO_EXPRESSO_500KM", texto) == 1.0


def test_numero_do_marcador_devolve_none_para_texto_sem_numero():
    assert verificar.numero_do_marcador("X", "X: muito caro") is None


def test_bloco_do_marcador_extrai_o_conteudo_entre_as_marcas():
    texto = ("LOG_DA_RETENTATIVA_INICIO\n"
             "tentativa canal=email\n"
             "falha canal=email motivo=timeout\n"
             "LOG_DA_RETENTATIVA_FIM\n")
    bloco = verificar.bloco_do_marcador("LOG_DA_RETENTATIVA", texto)
    assert bloco.splitlines() == ["tentativa canal=email",
                                  "falha canal=email motivo=timeout"]


def test_bloco_do_marcador_devolve_vazio_quando_nao_ha_bloco():
    assert verificar.bloco_do_marcador("LOG_DA_RETENTATIVA", "nada") == ""


def test_testes_verdes_le_a_saida_do_pytest():
    assert verificar.testes_verdes("22 passed in 0.30s") == (22, False)
    assert verificar.testes_verdes("2 failed, 20 passed in 0.4s") == (20, True)


def test_testes_verdes_le_a_saida_do_vitest():
    assert verificar.testes_verdes(" Tests  29 passed (29)") == (29, False)


def test_testes_verdes_admite_nao_reconhecer_o_formato():
    assert verificar.testes_verdes("comando não encontrado") == (None, False)
