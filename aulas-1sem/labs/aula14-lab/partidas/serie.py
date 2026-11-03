"""Série: o mesmo confronto ainda aberto, no mesmo campus, há menos de 48 horas."""

from __future__ import annotations

from datetime import timedelta

ABERTOS = {"ABERTO", "CONFIRMADO", "EM_JOGO"}


def normalizar(texto):
    return " ".join(str(texto).strip().split()).casefold()


def eh_serie(anterior, modalidade, campus, agora):
    """Passo 4 do README, slide "Missão 5. A série".

    anterior é um dict com modalidade, campus, status e criado_em.
    ABERTOS, normalizar e timedelta já estão neste arquivo.
    Substitua só esta função. Não apague o import.
    """
    return False
