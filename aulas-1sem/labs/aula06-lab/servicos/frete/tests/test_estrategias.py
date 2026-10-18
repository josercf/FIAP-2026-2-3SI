"""Testes das lacunas TODO-1 e TODO-2: o protocolo e as três estratégias.

Estes testes **já vêm escritos e falhando**. Não é engano: é a pirâmide de
testes trabalhando a favor de vocês. Cada lacuna preenchida acende um teste,
e a suíte inteira verde é o critério de aceitação do laboratório.

A rota de referência do laboratório é `SAO -> LDB`, 500 km, com 100 kg de
carga. Todos os valores esperados aqui saem da tabela de preços congelada
na docstring de `app/estrategias.py`.
"""

import pytest

from app.estrategias import (
    Cotacao,
    EstrategiaFrete,
    FreteEconomico,
    FreteExpresso,
    FretePadrao,
    valor_base,
)

DISTANCIA_REFERENCIA_KM = 500.0
PESO_REFERENCIA_KG = 100.0


def test_protocolo_declara_cotar_e_modalidade():
    """TODO-1: o contrato comum precisa declarar os dois membros.

    Um `Protocol` vazio aceita qualquer objeto e não serve de contrato
    nenhum, por isso o teste olha os membros declarados em vez de fazer um
    `isinstance` que passaria de graça.
    """
    assert hasattr(EstrategiaFrete, "cotar"), (
        "TODO-1: o protocolo EstrategiaFrete precisa declarar o método cotar")
    assert "modalidade" in getattr(EstrategiaFrete, "__annotations__", {}), (
        "TODO-1: o protocolo EstrategiaFrete precisa declarar o atributo "
        "modalidade: str")


@pytest.mark.parametrize("classe", [FreteExpresso, FreteEconomico, FretePadrao])
def test_cada_estrategia_cumpre_o_protocolo(classe):
    """TODO-1 e TODO-2: as três classes precisam servir como EstrategiaFrete."""
    estrategia = classe()
    assert isinstance(estrategia, EstrategiaFrete)
    assert isinstance(estrategia.modalidade, str) and estrategia.modalidade


@pytest.mark.parametrize("classe,valor,prazo", [
    (FreteExpresso, 545.00, 1),
    (FreteEconomico, 265.00, 4),
    (FretePadrao, 380.00, 2),
])
def test_valor_e_prazo_na_rota_de_referencia(classe, valor, prazo):
    """TODO-2: os números da tabela de preços, na rota SAO -> LDB com 100 kg."""
    cotacao = classe().cotar(DISTANCIA_REFERENCIA_KM, PESO_REFERENCIA_KG)
    assert isinstance(cotacao, Cotacao)
    assert cotacao.valor == pytest.approx(valor, abs=0.01)
    assert cotacao.prazo_dias == prazo
    assert cotacao.modalidade == classe.modalidade


def test_expresso_e_sempre_mais_caro_e_mais_rapido_que_economico():
    """A regra de negócio que dá sentido às duas modalidades existirem.

    Vale para qualquer carga: se em alguma faixa o econômico ficasse mais
    caro que o expresso, a tabela comercial estaria errada.
    """
    for distancia in (120.0, 500.0, 1960.0):
        for peso in (5.0, 100.0, 2000.0):
            rapido = FreteExpresso().cotar(distancia, peso)
            barato = FreteEconomico().cotar(distancia, peso)
            assert rapido.valor > barato.valor
            assert rapido.prazo_dias < barato.prazo_dias


def test_prazo_minimo_do_expresso_e_de_um_dia():
    """Entrega no mesmo dia não existe na LogiTech: o piso é um dia."""
    cotacao = FreteExpresso().cotar(12.0, 1.0)
    assert cotacao.prazo_dias == 1


def test_valor_base_arredonda_em_duas_casas():
    """Função de apoio congelada: cotação em reais não tem terceira casa."""
    assert valor_base(333.0, 7.0, 0.37, 0.19) == 124.54
