"""Testes das estratégias de frete. Vêm prontos e verdes: são o modelo.

CONGELADO. Não é tarefa, mas é o arquivo para ler antes de escrever o seu.

Repare no que **não** existe aqui: nenhum dublê. As estratégias são funções
puras disfarçadas de classe, recebem dois números e devolvem um objeto. Não
há colaborador para substituir, então não há nada para dublar.

Essa é a primeira regra de higiene de teste de unidade, e ela economiza mais
tempo do que qualquer biblioteca de mock: **dublê só onde há dependência de
verdade**. Mock em código puro é ruído que ninguém consegue ler daqui a seis
meses, e que passa a falhar quando você refatora sem mudar comportamento.

O arquivo também mostra o formato que a suíte inteira usa:

- `@pytest.mark.parametrize` para varrer casos que só mudam de número;
- um `assert` por comportamento, e não um `assert` gigante com `and`;
- nome de teste que diz a regra de negócio, e não o nome do método testado.
"""

import pytest

from app.estrategias import (
    Cotacao,
    FreteEconomico,
    FreteExpresso,
    FretePadrao,
    valor_base,
)

# Rota de referência do laboratório: SAO -> LDB, 500 km, com 100 kg de carga.
DISTANCIA_REFERENCIA_KM = 500.0
PESO_REFERENCIA_KG = 100.0


@pytest.mark.parametrize("estrategia, valor_esperado", [
    (FreteExpresso(), 545.00),
    (FreteEconomico(), 265.00),
    (FretePadrao(), 380.00),
])
def test_valor_da_rota_de_referencia(estrategia, valor_esperado):
    """Cada modalidade cobra o valor da tabela comercial na rota de referência."""
    cotacao = estrategia.cotar(DISTANCIA_REFERENCIA_KM, PESO_REFERENCIA_KG)
    assert cotacao.valor == pytest.approx(valor_esperado)


@pytest.mark.parametrize("estrategia, prazo_esperado", [
    (FreteExpresso(), 1),
    (FreteEconomico(), 4),
    (FretePadrao(), 2),
])
def test_prazo_da_rota_de_referencia(estrategia, prazo_esperado):
    """O prazo prometido em cada modalidade na rota de referência."""
    cotacao = estrategia.cotar(DISTANCIA_REFERENCIA_KM, PESO_REFERENCIA_KG)
    assert cotacao.prazo_dias == prazo_esperado


def test_expresso_nunca_promete_menos_de_um_dia():
    """Rota curta não vira entrega no mesmo instante: o piso é um dia.

    Caso de borda que o cálculo `ceil(distancia / 700)` devolveria como zero
    para qualquer rota abaixo de um quilômetro. O `max(1, ...)` existe por
    causa disso, e é este teste que impede alguém de removê-lo achando que é
    código morto.
    """
    assert FreteExpresso().cotar(0.5, 10.0).prazo_dias == 1


def test_a_cotacao_e_imutavel():
    """Cotação emitida não se altera: emite-se outra.

    `Cotacao` é um `dataclass(frozen=True)`, e este teste documenta a
    decisão. Sem ele, alguém tira o `frozen` para "facilitar um ajuste" e
    ninguém percebe.
    """
    cotacao = FretePadrao().cotar(DISTANCIA_REFERENCIA_KM, PESO_REFERENCIA_KG)
    with pytest.raises(Exception):
        cotacao.valor = 1.0


def test_valor_base_arredonda_em_duas_casas():
    """Dinheiro não tem terceira casa decimal."""
    assert valor_base(333.0, 7.0, 0.333, 0.777) == 116.33


def test_a_modalidade_viaja_junto_com_a_cotacao():
    """Quem recebe a cotação sabe de qual modalidade ela é, sem consultar nada."""
    cotacao = FreteEconomico().cotar(DISTANCIA_REFERENCIA_KM, PESO_REFERENCIA_KG)
    assert isinstance(cotacao, Cotacao)
    assert cotacao.modalidade == "economico"
