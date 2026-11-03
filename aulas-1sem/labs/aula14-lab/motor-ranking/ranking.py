"""Strategy de faixa da ArenaLog.

A tabela de pontos é um objeto. O teste troca ou espiona essa tabela
sem editar a rota HTTP.
"""

from __future__ import annotations

PONTOS_BASE = {
    "FPS": 3,
    "MOBA": 3,
    "LUTE": 2,
    "ESPORTE": 2,
    "CARTAS": 1,
}


class ModalidadeDesconhecida(Exception):
    def __init__(self, modalidade):
        super().__init__(str(modalidade))
        self.modalidade = str(modalidade)


def normalizar(texto):
    return " ".join(str(texto).strip().split()).casefold()


class TabelaDePesos:
    def __init__(self, pontos=None):
        self._pontos = dict(PONTOS_BASE if pontos is None else pontos)

    def pontos_base(self, modalidade):
        chave = str(modalidade).strip().upper()
        if chave not in self._pontos:
            raise ModalidadeDesconhecida(chave)
        return self._pontos[chave]


def faixa_de(pontos):
    if pontos >= 5:
        return "LENDARIO", 8
    if pontos == 4:
        return "OURO", 24
    if pontos >= 2:
        return "PRATA", 72
    return "BRONZE", 168


def calcular(modalidade, campus, serie, tabela, campi_rivais):
    """Missão 3.

    Some o pontos-base da modalidade, +2 se o campus estiver na lista de
    rivalidade e +1 se serie for verdadeira. A comparação do campus ignora
    maiúsculas e espaços repetidos.

    Devolva {"pontos", "faixa", "janelaHoras"} usando faixa_de.
    Modalidade desconhecida sobe como ModalidadeDesconhecida, vinda da tabela.
    """
    raise NotImplementedError(
        "Missão 3: implementar a Strategy de faixa em ranking.calcular."
    )
