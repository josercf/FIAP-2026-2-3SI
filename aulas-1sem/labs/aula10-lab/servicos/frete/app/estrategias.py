"""As modalidades de frete da LogiTech, uma classe por algoritmo.

CONGELADO. Não é tarefa da Aula 10.

Este arquivo é o que a Aula 06 entregou, com as lacunas `TODO-1` e `TODO-2`
daquele laboratório já preenchidas. Ele está aqui porque hoje o exercício é
o oposto: em vez de escrever a regra, você escreve o **teste** que prova que
ela está certa e que continua certa amanhã.

O módulo é de propósito **puro**: não importa FastAPI, não importa Pydantic,
não conhece HTTP e não abre socket. É o que permite testar a regra de
negócio sem subir servidor nenhum.

Tabela de preços da LogiTech, congelada (as evidências do laboratório e o
verificador dependem destes números):

| Modalidade  | Custo por km | Custo por kg | Prazo em dias                    |
|-------------|--------------|--------------|----------------------------------|
| expresso    | 0,85         | 1,20         | ceil(distancia / 700), mínimo 1  |
| economico   | 0,42         | 0,55         | ceil(distancia / 350) + 2        |
| padrao      | 0,60         | 0,80         | ceil(distancia / 500) + 1        |

Conferência rápida na rota de referência (500 km, 100 kg):
expresso 545,00 em 1 dia; economico 265,00 em 4 dias; padrao 380,00 em 2 dias.
"""

from dataclasses import dataclass
from math import ceil
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class Cotacao:
    """O resultado de uma cotação, no vocabulário do case.

    Congelado (`frozen=True`) de propósito: cotação emitida não se altera,
    emite-se outra.
    """

    valor: float
    prazo_dias: int
    modalidade: str


def valor_base(distancia_km: float, peso_kg: float,
               custo_por_km: float, custo_por_kg: float) -> float:
    """Fórmula comum a todas as modalidades, arredondada em duas casas."""
    return round(distancia_km * custo_por_km + peso_kg * custo_por_kg, 2)


@runtime_checkable
class EstrategiaFrete(Protocol):
    """Contrato que toda modalidade de frete cumpre."""

    modalidade: str

    def cotar(self, distancia_km: float, peso_kg: float) -> Cotacao:
        """Cota uma carga de `peso_kg` percorrendo `distancia_km`."""
        ...


class FreteExpresso:
    """Modalidade mais cara, com o menor prazo. Prioridade na roteirização."""

    modalidade = "expresso"
    custo_por_km = 0.85
    custo_por_kg = 1.20

    def cotar(self, distancia_km: float, peso_kg: float) -> Cotacao:
        return Cotacao(
            valor=valor_base(distancia_km, peso_kg,
                             self.custo_por_km, self.custo_por_kg),
            prazo_dias=max(1, ceil(distancia_km / 700)),
            modalidade=self.modalidade,
        )


class FreteEconomico:
    """Modalidade mais barata, com o maior prazo. Consolida carga em rota."""

    modalidade = "economico"
    custo_por_km = 0.42
    custo_por_kg = 0.55

    def cotar(self, distancia_km: float, peso_kg: float) -> Cotacao:
        return Cotacao(
            valor=valor_base(distancia_km, peso_kg,
                             self.custo_por_km, self.custo_por_kg),
            prazo_dias=ceil(distancia_km / 350) + 2,
            modalidade=self.modalidade,
        )


class FretePadrao:
    """O meio-termo contratado pela maior parte dos clientes da LogiTech."""

    modalidade = "padrao"
    custo_por_km = 0.60
    custo_por_kg = 0.80

    def cotar(self, distancia_km: float, peso_kg: float) -> Cotacao:
        return Cotacao(
            valor=valor_base(distancia_km, peso_kg,
                             self.custo_por_km, self.custo_por_kg),
            prazo_dias=ceil(distancia_km / 500) + 1,
            modalidade=self.modalidade,
        )
