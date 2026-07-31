"""Testes da lacuna TODO-3: o registro de modalidades.

O registro é o que fecha o serviço para modificação e o abre para extensão.
Se estes testes passam, acrescentar uma modalidade nova deixou de ser
"editar a rota" e virou "acrescentar uma linha no registro".
"""

import pytest

from app.estrategias import Cotacao, EstrategiaFrete
from app.registro import REGISTRO, modalidades, obter

MODALIDADES_ORIGINAIS = {"expresso", "economico", "padrao"}


def test_as_tres_modalidades_originais_estao_registradas():
    """TODO-3: sem elas registradas, a rota não tem a quem delegar."""
    assert MODALIDADES_ORIGINAIS.issubset(set(REGISTRO)), (
        "TODO-3: faltam modalidades no registro. Encontradas: %s"
        % sorted(REGISTRO))


def test_obter_devolve_uma_estrategia_de_verdade():
    """O registro guarda instâncias prontas, não nomes de classe."""
    estrategia = obter("expresso")
    assert isinstance(estrategia, EstrategiaFrete)
    assert isinstance(estrategia.cotar(500.0, 100.0), Cotacao)


def test_obter_recusa_modalidade_desconhecida():
    """Modalidade inexistente vira `KeyError`, e a rota traduz para 422."""
    with pytest.raises(KeyError):
        obter("teletransporte")


def test_modalidades_vem_ordenado_e_sem_repeticao():
    """A rota `GET /api/v1/frete/modalidades` publica esta lista."""
    lista = modalidades()
    assert lista == sorted(lista)
    assert len(lista) == len(set(lista))
    assert len(lista) >= 3
