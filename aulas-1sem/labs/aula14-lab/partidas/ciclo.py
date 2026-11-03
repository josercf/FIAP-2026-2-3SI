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
    """Missão 4.

    Devolva o destino quando a passagem estiver em ACEITOS.
    Destino igual ao atual também é recusa.
    Caso contrário, levante TransicaoRecusada.
    """
    raise NotImplementedError("Missão 4: implementar transicionar em ciclo.py.")
