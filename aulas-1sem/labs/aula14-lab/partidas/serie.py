"""Série: o mesmo confronto ainda aberto, no mesmo campus, há menos de 48 horas."""

from __future__ import annotations

from datetime import timedelta

ABERTOS = {"ABERTO", "CONFIRMADO", "EM_JOGO"}


def normalizar(texto):
    return " ".join(str(texto).strip().split()).casefold()


def eh_serie(anterior, modalidade, campus, agora):
    """Missão 5.

    anterior é um dict com modalidade, campus, status e criado_em.
    Conta como série quando:
    - a modalidade é a mesma
    - o campus é o mesmo, ignorando maiúsculas e espaços repetidos
    - o status está em ABERTOS (ENCERRADO e CANCELADO não contam)
    - agora - criado_em é estritamente menor que 48 horas
      (47h59 conta, 48h00 não conta)
    """
    return False
