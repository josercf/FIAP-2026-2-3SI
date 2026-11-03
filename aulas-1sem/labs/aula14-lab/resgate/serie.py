"""Cópia resolvida de partidas/serie.py."""

from __future__ import annotations

from datetime import timedelta

ABERTOS = {"ABERTO", "CONFIRMADO", "EM_JOGO"}


def normalizar(texto):
    return " ".join(str(texto).strip().split()).casefold()


def eh_serie(anterior, modalidade, campus, agora):
    if str(anterior.get("modalidade", "")).upper() != str(modalidade).upper():
        return False
    if normalizar(anterior.get("campus", "")) != normalizar(campus):
        return False
    if anterior.get("status") not in ABERTOS:
        return False
    return (agora - anterior["criado_em"]) < timedelta(hours=48)
