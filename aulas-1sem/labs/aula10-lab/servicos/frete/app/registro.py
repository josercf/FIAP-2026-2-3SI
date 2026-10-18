"""Registro de modalidades de frete: o Open/Closed da Aula 06, já pronto.

CONGELADO. Não é tarefa da Aula 10.

A rota HTTP não sabe quais modalidades existem: ela pergunta ao registro
qual estratégia atende aquele nome e executa. Acrescentar uma modalidade é
acrescentar uma linha aqui.

Assim como `estrategias.py`, este módulo não importa FastAPI: o registro é
regra de negócio, não detalhe de transporte.
"""

from .estrategias import (
    EstrategiaFrete,
    FreteEconomico,
    FreteExpresso,
    FretePadrao,
)

REGISTRO: dict[str, EstrategiaFrete] = {}
"""Mapa `nome da modalidade -> instância da estratégia`."""


def registrar(estrategia: EstrategiaFrete) -> None:
    """Põe uma estratégia no registro, indexada pelo próprio `modalidade`.

    Recusa nome repetido de propósito: duas estratégias disputando a mesma
    modalidade é erro de programação que se descobre na importação do
    módulo, e não em produção, com o cliente esperando a cotação.
    """
    nome = estrategia.modalidade
    if nome in REGISTRO:
        raise ValueError("modalidade já registrada: %s" % nome)
    REGISTRO[nome] = estrategia


def obter(modalidade: str) -> EstrategiaFrete:
    """Devolve a estratégia de uma modalidade. Levanta `KeyError` se não houver."""
    try:
        return REGISTRO[modalidade]
    except KeyError:
        raise KeyError(
            "modalidade não suportada: %r. Disponíveis: %s"
            % (modalidade, ", ".join(modalidades()))) from None


def modalidades() -> list[str]:
    """Os nomes registrados, em ordem alfabética."""
    return sorted(REGISTRO)


registrar(FreteExpresso())
registrar(FreteEconomico())
registrar(FretePadrao())
