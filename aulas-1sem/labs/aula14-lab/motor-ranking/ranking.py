"""Conta da faixa da ArenaLog.

A tabela de pontos é um objeto. O teste observa qual chave ela recebeu
sem editar a rota HTTP. A função pronta está no passo 2 do README.
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
    """Passo 2 do README, slide "Missão 3. A faixa".

    Substitua só esta função. A primeira linha tem que chamar
    tabela.pontos_base. faixa_de e normalizar já existem neste arquivo.
    """
    raise NotImplementedError(
        "Passo 2: cole calcular a partir do README ou do slide da Missão 3."
    )
