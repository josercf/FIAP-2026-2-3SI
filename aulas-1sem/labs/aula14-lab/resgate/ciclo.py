"""Cópia resolvida de partidas/ciclo.py."""

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
    if destino not in ACEITOS.get(atual, set()):
        raise TransicaoRecusada(atual, destino)
    return destino
