"""
Strategy: quem decide para qual provedor a chamada vai.

A fachada sabe *que* existe uma ordem de tentativa. Ela não sabe *como* essa
ordem é decidida, e é exatamente essa ignorância que permite trocar a
política de roteamento por variável de ambiente, sem tocar em uma linha da
fachada nem dos provedores.

Quatro políticas, todas com o mesmo formato de entrada e saída:

    preferir-remoto     qualidade primeiro, custo depois
    preferir-local      custo e privacidade primeiro
    somente-local       nenhum dado da LogiTech sai da rede da empresa
    por-tamanho         pergunta curta vai ao local, pergunta longa ao remoto

A última é a que mostra por que isto é Strategy e não uma lista ordenada em
arquivo de configuração: a decisão depende **da requisição**, e muda a cada
chamada.
"""

from __future__ import annotations

import os
from typing import Protocol

from provedores import ProvedorDeIA


class EstrategiaDeRoteamento(Protocol):
    """Recebe os provedores disponíveis e devolve a ordem de tentativa."""

    nome: str

    def ordenar(self, provedores: list[ProvedorDeIA],
                pergunta: str) -> list[ProvedorDeIA]: ...


def _por_nome(provedores: list[ProvedorDeIA], ordem: list[str]) -> list[ProvedorDeIA]:
    """Ordena os provedores conforme uma lista de nomes, ignorando os que não
    existem e mantendo no fim os que a lista não citou."""
    indice = {p.nome: p for p in provedores}
    escolhidos = [indice[n] for n in ordem if n in indice]
    escolhidos += [p for p in provedores if p.nome not in ordem]
    return escolhidos


class PreferirRemoto:
    """O provedor pago primeiro; o local é a rede de segurança.

    É a política padrão da LogiTech: o modelo remoto responde melhor às
    perguntas de atendimento, e o local existe para a operação não parar
    quando a cota acaba ou a API cai.
    """

    nome = "preferir-remoto"

    def ordenar(self, provedores, pergunta):
        return _por_nome(provedores, ["remoto", "local"])


class PreferirLocal:
    """O local primeiro, por custo e por latência. O remoto socorre."""

    nome = "preferir-local"

    def ordenar(self, provedores, pergunta):
        return _por_nome(provedores, ["local", "remoto"])


class SomenteLocal:
    """Nada sai da rede da LogiTech.

    Política de conformidade, não de custo: existe para os contextos em que a
    pergunta carrega dado de cliente. Note que ela não "prefere" o local, ela
    **remove** o remoto da lista: preferência não é controle.
    """

    nome = "somente-local"

    def ordenar(self, provedores, pergunta):
        return [p for p in provedores if p.nome == "local"]


class PorTamanhoDaPergunta:
    """Decide a cada requisição, olhando o tamanho da pergunta.

    Pergunta curta ("onde está o pedido 4471?") tem resposta boa no modelo
    pequeno e local. Pergunta longa, com contexto, vale o custo do remoto.
    O limiar vem de LOGITECH_IA_LIMIAR_CARACTERES.
    """

    nome = "por-tamanho"

    def __init__(self) -> None:
        self.limiar = int(os.environ.get("LOGITECH_IA_LIMIAR_CARACTERES", "280"))

    def ordenar(self, provedores, pergunta):
        if len(pergunta) <= self.limiar:
            return _por_nome(provedores, ["local", "remoto"])
        return _por_nome(provedores, ["remoto", "local"])


ESTRATEGIAS: dict[str, type] = {
    PreferirRemoto.nome: PreferirRemoto,
    PreferirLocal.nome: PreferirLocal,
    SomenteLocal.nome: SomenteLocal,
    PorTamanhoDaPergunta.nome: PorTamanhoDaPergunta,
}


def escolher_estrategia(nome: str | None = None) -> EstrategiaDeRoteamento:
    """Instancia a estratégia pedida, caindo na padrão quando o nome não
    existe. Cair em silêncio seria pior: o nome inválido é registrado."""
    pedido = (nome or os.environ.get("LOGITECH_IA_ESTRATEGIA")
              or PreferirRemoto.nome).strip()
    classe = ESTRATEGIAS.get(pedido)
    if classe is None:
        print("[ROTEAMENTO] estratégia '%s' não existe; usando '%s'. "
              "Disponíveis: %s" % (pedido, PreferirRemoto.nome,
                                   ", ".join(sorted(ESTRATEGIAS))), flush=True)
        classe = PreferirRemoto
    return classe()
