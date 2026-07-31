"""Tabela de distâncias entre os centros de distribuição da LogiTech.

Não é tarefa do laboratório: é dado de apoio, congelado, para que o cálculo
de frete seja determinístico e as evidências de todo mundo batam com as do
verificador. Os códigos são os dos centros de distribuição da LogiTech, e a
distância é a rodoviária arredondada que o roteirizador da empresa devolve.

A rota de referência do laboratório é `SAO -> LDB`, com 500 km exatos: é
sobre ela que `docs/EVIDENCIAS.md` pede os valores.
"""

DISTANCIA_PADRAO_KM = 750.0
"""Usada quando o par origem/destino não está na tabela. A LogiTech trata
rota desconhecida como rota média, e não como erro, para não derrubar a
cotação de um cliente novo no meio da negociação."""

DISTANCIAS_KM = {
    ("SAO", "LDB"): 500.0,
    ("SAO", "RIO"): 430.0,
    ("SAO", "CWB"): 410.0,
    ("SAO", "BHZ"): 590.0,
    ("SAO", "POA"): 1110.0,
    ("SAO", "SSA"): 1960.0,
    ("RIO", "BHZ"): 440.0,
    ("RIO", "VIX"): 520.0,
    ("CWB", "POA"): 710.0,
    ("BHZ", "SSA"): 1370.0,
}


def distancia_km(origem: str, destino: str) -> float:
    """Devolve a distância entre dois centros de distribuição, em quilômetros.

    A tabela é simétrica: a LogiTech não cobra diferente por sentido de
    viagem, então `SAO -> RIO` e `RIO -> SAO` devolvem o mesmo valor. Par
    ausente cai em `DISTANCIA_PADRAO_KM`.
    """
    o = origem.strip().upper()
    d = destino.strip().upper()
    if (o, d) in DISTANCIAS_KM:
        return DISTANCIAS_KM[(o, d)]
    if (d, o) in DISTANCIAS_KM:
        return DISTANCIAS_KM[(d, o)]
    return DISTANCIA_PADRAO_KM
