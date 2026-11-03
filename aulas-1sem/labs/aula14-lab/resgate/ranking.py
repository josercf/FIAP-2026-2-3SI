"""Cópia resolvida de motor-ranking/ranking.py. Use só se a mesa travar."""

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
    pontos = tabela.pontos_base(modalidade)
    campus_norm = normalizar(campus)
    if any(normalizar(nome) == campus_norm for nome in campi_rivais):
        pontos += 2
    if serie:
        pontos += 1
    faixa, janela = faixa_de(pontos)
    return {"pontos": pontos, "faixa": faixa, "janelaHoras": janela}
