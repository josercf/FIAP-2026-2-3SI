"""As modalidades de frete da LogiTech, uma classe por algoritmo.

Aqui moram as lacunas TODO-1 e TODO-2 do laboratório.

Este módulo é de propósito **puro**: não importa FastAPI, não importa
Pydantic, não conhece HTTP. É o que permite testar a regra de negócio sem
subir servidor nenhum, e é o que permite o `verificar.py` (que não tem
dependência externa) importar este arquivo direto.

Tabela de preços da LogiTech, congelada (não altere estes números, as
evidências do laboratório dependem deles):

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
    emite-se outra. É o mesmo raciocínio de objeto de valor que vocês viram
    na linguagem ubíqua da Aula 01.
    """

    valor: float
    prazo_dias: int
    modalidade: str


def valor_base(distancia_km: float, peso_kg: float,
               custo_por_km: float, custo_por_kg: float) -> float:
    """Fórmula comum a todas as modalidades, arredondada em duas casas.

    Vem pronta: o que o laboratório exercita é a **estrutura** que escolhe o
    algoritmo, não a aritmética dele.
    """
    return round(distancia_km * custo_por_km + peso_kg * custo_por_kg, 2)


# ---------------------------------------------------------------------------
# TODO-1: o contrato comum das modalidades
# ---------------------------------------------------------------------------
@runtime_checkable
class EstrategiaFrete(Protocol):
    """Contrato que toda modalidade de frete precisa cumprir.

    TODO-1: declare aqui o contrato comum. Um `Protocol` do módulo `typing`
    descreve o formato esperado sem obrigar herança: quem tiver os membros
    certos já é uma `EstrategiaFrete`.

    O contrato precisa ter, exatamente:

    - o atributo `modalidade: str`, o nome pelo qual a API conhece a
      modalidade (`"expresso"`, `"economico"`, ...);
    - o método `cotar(self, distancia_km: float, peso_kg: float) -> Cotacao`.

    Enquanto esta lacuna estiver aberta, `python3 verificar.py --criterio 1`
    reprova, porque o protocolo não declara `cotar`.
    """

    # Apague este `pass` e escreva o contrato descrito acima.
    pass


# ---------------------------------------------------------------------------
# TODO-2: uma classe por algoritmo de frete
# ---------------------------------------------------------------------------
class FreteExpresso:
    """Modalidade mais cara, com o menor prazo. Prioridade na roteirização."""

    modalidade = "expresso"
    custo_por_km = 0.85
    custo_por_kg = 1.20

    def cotar(self, distancia_km: float, peso_kg: float) -> Cotacao:
        # TODO-2: devolva uma `Cotacao` usando `valor_base` com os custos
        # desta classe e o prazo `ceil(distancia_km / 700)`, com mínimo de
        # 1 dia. `ceil` já está importado no topo do arquivo.
        raise NotImplementedError(
            "TODO-2: FreteExpresso.cotar ainda não foi implementado")


class FreteEconomico:
    """Modalidade mais barata, com o maior prazo. Consolida carga em rota."""

    modalidade = "economico"
    custo_por_km = 0.42
    custo_por_kg = 0.55

    def cotar(self, distancia_km: float, peso_kg: float) -> Cotacao:
        # TODO-2: prazo `ceil(distancia_km / 350) + 2`.
        raise NotImplementedError(
            "TODO-2: FreteEconomico.cotar ainda não foi implementado")


class FretePadrao:
    """O meio-termo contratado pela maior parte dos clientes da LogiTech."""

    modalidade = "padrao"
    custo_por_km = 0.60
    custo_por_kg = 0.80

    def cotar(self, distancia_km: float, peso_kg: float) -> Cotacao:
        # TODO-2: prazo `ceil(distancia_km / 500) + 1`.
        raise NotImplementedError(
            "TODO-2: FretePadrao.cotar ainda não foi implementado")
