"""Ciclo de vida de um desafio. Função pura, fora do HTTP."""

from __future__ import annotations


class TransicaoRecusada(Exception):
    def __init__(self, atual, destino):
        super().__init__(f"{atual} -> {destino}")
        self.atual = atual
        self.destino = destino


ACEITOS = {
    "ABERTO": {"CONFIRMADO", "CANCELADO"},
    "CONFIRMADO": {"EM_JOGO", "CANCELADO"},
    "EM_JOGO": {"ENCERRADO", "CANCELADO"},
    "ENCERRADO": set(),
    "CANCELADO": set(),
}


def transicionar(atual, destino):
    """Passo 3 do README, slide "Missão 4. O status".

    ACEITOS já está neste arquivo. Substitua só esta função.
    """
    raise NotImplementedError(
        "Passo 3: cole transicionar a partir do README ou do slide da Missão 4."
    )
