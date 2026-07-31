"""As regras de negócio que a Aula 10 põe sob teste.

CONGELADO. Não é tarefa da Aula 10. O que você escreve são os testes.

`CotadorDePedido` é o caso de uso "cotar o frete de um pedido que já existe".
Ele não sabe HTTP, não sabe JSON e não abre socket. Tudo o que ele conhece
de mundo externo chega pelo construtor:

    CotadorDePedido(cliente, tabela=..., registro_obter=...)

Isso tem nome, é o mesmo princípio da injeção de dependência que vocês viram
na Aula 05, e tem uma consequência prática que só aparece hoje: **um objeto
que recebe suas dependências é um objeto que você consegue testar sozinho**.

As cinco regras, na ordem em que o método aplica:

1. O identificador precisa casar com `PED-` seguido de quatro dígitos. Se
   não casar, levanta `PedidoInvalido` **sem consultar o serviço de
   Pedidos**. Chamada de rede que se sabe inútil não se faz.
2. O pedido é buscado uma única vez por instância do cotador. A segunda
   cotação do mesmo pedido reaproveita o que já veio.
3. Carga acima de `LIMITE_KG` é recusada com `CargaAcimaDoLimite`. A frota
   da LogiTech não tem veículo para isso.
4. A distância vem da tabela, sempre consultada como `km(origem, destino)`,
   na ordem do pedido.
5. Sobre o valor da estratégia incidem duas regras comerciais:
   - carga a partir de `PESO_CARGA_FECHADA` kg ganha `DESCONTO_CARGA_FECHADA`
     de desconto, porque ocupa o caminhão inteiro e dispensa consolidação;
   - rota acima de `DISTANCIA_PERNOITE_KM` km soma **um dia** ao prazo,
     porque a legislação obriga o motorista a parar para descanso.

Repare no formato das regras 1, 2 e 4: elas não falam do resultado, falam de
**o que o objeto faz com seus colaboradores**. Nenhuma asserção sobre o
número devolvido consegue provar que a regra 2 está viva. É essa a fronteira
entre Stub e Mock, e é literalmente o que o laboratório de hoje exercita.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from .cliente_pedidos import ClientePedidos, PedidoResumo
from .distancias import TabelaDistancias
from .estrategias import EstrategiaFrete
from .registro import obter as obter_estrategia

FORMATO_PEDIDO = re.compile(r"^PED-\d{4}$")

LIMITE_KG = 30000.0
"""Capacidade máxima que a frota da LogiTech transporta em um pedido."""

PESO_CARGA_FECHADA = 1000.0
"""A partir daqui a carga ocupa o veículo inteiro e dispensa consolidação."""

DESCONTO_CARGA_FECHADA = 0.08
"""Desconto comercial da carga fechada, 8 por cento sobre o valor da tabela."""

DISTANCIA_PERNOITE_KM = 1000.0
"""Acima disso o motorista para para descanso e o prazo ganha um dia."""


class PedidoInvalido(ValueError):
    """O identificador não tem o formato `PED-0000`."""


class CargaAcimaDoLimite(ValueError):
    """O pedido pesa mais do que a frota consegue transportar."""


class ModalidadeNaoSuportada(ValueError):
    """A modalidade pedida não está no registro."""


@dataclass(frozen=True)
class CotacaoDePedido:
    """O que o caso de uso devolve, com os dados que sustentam o número.

    Devolver `peso_kg` e `distancia_km` junto não é enfeite: é o que permite
    a tela do portal e a auditoria da LogiTech explicarem de onde veio o
    valor sem refazer a conta.
    """

    pedido_id: str
    modalidade: str
    valor: float
    prazo_dias: int
    peso_kg: float
    distancia_km: float
    carga_fechada: bool


class CotadorDePedido:
    """Cota o frete de um pedido já existente na LogiTech."""

    def __init__(self, cliente: ClientePedidos,
                 tabela: TabelaDistancias | None = None,
                 registro_obter: Callable[[str], EstrategiaFrete] | None = None) -> None:
        self._cliente = cliente
        self._tabela = tabela if tabela is not None else TabelaDistancias()
        self._obter = registro_obter if registro_obter is not None else obter_estrategia
        self._cache: dict[str, PedidoResumo] = {}

    # -- colaboração com o serviço de Pedidos --------------------------------
    def _buscar_pedido(self, pedido_id: str) -> PedidoResumo:
        """Busca o pedido no serviço vizinho, uma vez por instância.

        A LogiTech cota o mesmo pedido em três modalidades para mostrar as
        opções ao cliente. Sem esta memória seriam três chamadas de rede
        para responder uma tela só.
        """
        if pedido_id not in self._cache:
            self._cache[pedido_id] = self._cliente.buscar(pedido_id)
        return self._cache[pedido_id]

    # -- caso de uso ---------------------------------------------------------
    def cotar(self, pedido_id: str, modalidade: str) -> CotacaoDePedido:
        """Cota o frete de um pedido em uma modalidade."""
        identificador = (pedido_id or "").strip().upper()
        if not FORMATO_PEDIDO.match(identificador):
            raise PedidoInvalido(
                "identificador fora do formato PED-0000: %r" % pedido_id)

        pedido = self._buscar_pedido(identificador)

        if pedido.peso_kg > LIMITE_KG:
            raise CargaAcimaDoLimite(
                "%s pesa %.1f kg e o limite da frota é %.1f kg"
                % (identificador, pedido.peso_kg, LIMITE_KG))

        try:
            estrategia = self._obter(modalidade)
        except KeyError as erro:
            raise ModalidadeNaoSuportada(str(erro)) from None

        distancia = self._tabela.km(pedido.origem, pedido.destino)
        bruta = estrategia.cotar(distancia, pedido.peso_kg)

        carga_fechada = pedido.peso_kg >= PESO_CARGA_FECHADA
        valor = bruta.valor
        if carga_fechada:
            valor = round(valor * (1 - DESCONTO_CARGA_FECHADA), 2)

        prazo = bruta.prazo_dias
        if distancia > DISTANCIA_PERNOITE_KM:
            prazo += 1

        return CotacaoDePedido(
            pedido_id=identificador,
            modalidade=bruta.modalidade,
            valor=valor,
            prazo_dias=prazo,
            peso_kg=pedido.peso_kg,
            distancia_km=distancia,
            carga_fechada=carga_fechada,
        )
