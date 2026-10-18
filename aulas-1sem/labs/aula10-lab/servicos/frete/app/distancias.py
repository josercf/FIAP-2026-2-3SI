"""Tabela de distâncias entre os centros de distribuição da LogiTech.

CONGELADO. Não é tarefa da Aula 10.

Mudou uma coisa em relação à Aula 06, e a mudança é deliberada: lá isto era
uma função de módulo, `distancia_km(origem, destino)`. Aqui é uma **classe**,
`TabelaDistancias`, com o método `km(origem, destino)`.

O motivo é o assunto de hoje. Uma função de módulo importada direto só se
substitui em teste com `monkeypatch`, que reescreve o módulo por baixo de
quem chama. Uma colaboradora recebida no construtor se substitui declarando
outra no lugar, e é isso que permite o **Spy** do `TODO-3`: envolver a tabela
real, deixá-la responder de verdade e ainda assim conferir com quais
argumentos ela foi consultada.

Esse é o padrão geral: dependência injetada é dependência testável. Não é
sobre a biblioteca de mock; é sobre onde a dependência entra no objeto.
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


class TabelaDistancias:
    """Distância rodoviária entre dois centros de distribuição, em km.

    A tabela é simétrica: a LogiTech não cobra diferente por sentido de
    viagem, então `SAO -> RIO` e `RIO -> SAO` devolvem o mesmo número.

    Guarde essa simetria, porque ela é o coração do `TODO-3`: um cotador que
    consultasse a tabela com origem e destino **trocados** devolveria o valor
    certo mesmo assim. Nenhuma asserção sobre o resultado pegaria o erro. Só
    uma asserção sobre a chamada pega.
    """

    def __init__(self, tabela: dict | None = None,
                 padrao_km: float = DISTANCIA_PADRAO_KM) -> None:
        self._tabela = DISTANCIAS_KM if tabela is None else tabela
        self._padrao_km = padrao_km

    def km(self, origem: str, destino: str) -> float:
        """Devolve a distância entre dois centros. Par ausente cai no padrão."""
        o = origem.strip().upper()
        d = destino.strip().upper()
        if (o, d) in self._tabela:
            return self._tabela[(o, d)]
        if (d, o) in self._tabela:
            return self._tabela[(d, o)]
        return self._padrao_km
