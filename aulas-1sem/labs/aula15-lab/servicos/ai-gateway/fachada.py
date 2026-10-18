"""
A Fachada (Facade) do AI Gateway da LogiTech.

Este é o único objeto que o resto da plataforma conhece. Um serviço que
precisa de IA chama `responder(pergunta)` e recebe texto. Ele não sabe:

    quantos provedores existem,
    qual foi usado,
    que formato de payload cada um exige,
    onde a credencial mora,
    que houve cache,
    que houve fallback.

Sem a fachada, cada um dos seis serviços da plataforma teria a própria
integração: seis lugares para trocar quando o provedor mudar de formato, seis
credenciais espalhadas, seis implementações de retentativa, e nenhuma visão
de quanto a empresa gasta com IA. É essa multiplicação que o padrão elimina.

Facade e Strategy fazem coisas diferentes aqui, e vale separar:

    Facade    esconde a complexidade  -> uma porta de entrada só
    Strategy  troca o comportamento   -> qual provedor, decidido em tempo
                                          de execução, sem `if` na fachada
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from metricas import Metricas
from politicas import CacheDeRespostas, LimitadorDeTaxa
from provedores import ProvedorDeIA, ProvedorIndisponivel, RespostaDeIA
from roteamento import EstrategiaDeRoteamento


class TodosOsProvedoresIndisponiveis(RuntimeError):
    """Nenhum provedor da ordem conseguiu atender."""

    def __init__(self, motivos: dict[str, str]) -> None:
        super().__init__("nenhum provedor de IA respondeu")
        self.motivos = motivos


@dataclass
class ResultadoDoGateway:
    """A resposta, mais o que a operação precisa saber sobre ela."""

    conteudo: str
    modelo: str
    provedor: str
    tokens_estimados: int
    origem_do_cache: str | None      # "exato", "similaridade" ou None
    similaridade: float
    houve_fallback: bool
    tentativas: list[str]
    duracao_ms: int


class GatewayDeIA:
    """A fachada. Uma porta de entrada para toda a IA da plataforma."""

    def __init__(self, provedores: list[ProvedorDeIA],
                 estrategia: EstrategiaDeRoteamento,
                 cache: CacheDeRespostas,
                 limitador: LimitadorDeTaxa,
                 metricas: Metricas) -> None:
        self.provedores = provedores
        self.estrategia = estrategia
        self.cache = cache
        self.limitador = limitador
        self.metricas = metricas

    def estado_dos_provedores(self) -> dict[str, str]:
        """Diagnóstico barato, sem tocar a rede. Usado por `/health`."""
        return {
            p.nome: (p.por_que_indisponivel() or "aparentemente disponível")
            for p in self.provedores
        }

    async def responder(self, pergunta: str, modelo: str | None = None,
                        cliente: str = "anonimo") -> ResultadoDoGateway:
        """O caminho completo de uma pergunta.

        A ordem importa e é a mesma de qualquer gateway sério:

            1. limite de taxa   recusar cedo custa menos que recusar tarde
            2. cache            a chamada mais barata é a que não acontece
            3. roteamento       a estratégia decide a ordem de tentativa
            4. fallback         cada falha é registrada e a fila continua
        """
        comeco = time.perf_counter()
        self.metricas.registrar_requisicao()

        # 1. Limite de taxa. LimiteExcedido sobe para quem chamou.
        self.limitador.permitir(cliente)

        # 2. Cache.
        em_cache, tipo, nota = self.cache.consultar(pergunta)
        if em_cache is not None and tipo is not None:
            self.metricas.registrar_acerto_de_cache(tipo)
            return ResultadoDoGateway(
                conteudo=em_cache["conteudo"],
                modelo=em_cache["modelo"],
                provedor=em_cache["provedor"],
                tokens_estimados=em_cache["tokens_estimados"],
                origem_do_cache=tipo,
                similaridade=nota,
                houve_fallback=False,
                tentativas=[],
                duracao_ms=int((time.perf_counter() - comeco) * 1000),
            )
        self.metricas.registrar_erro_de_cache()

        # 3. Roteamento: a fachada não decide, ela pergunta.
        ordem = self.estrategia.ordenar(list(self.provedores), pergunta)
        if not ordem:
            raise TodosOsProvedoresIndisponiveis(
                {"(nenhum)": "a estratégia '%s' não deixou nenhum provedor "
                             "elegível" % self.estrategia.nome})

        # 4. Tentativa e fallback.
        motivos: dict[str, str] = {}
        tentados: list[str] = []
        resposta: RespostaDeIA | None = None

        for posicao, provedor in enumerate(ordem):
            tentados.append(provedor.nome)
            self.metricas.registrar_tentativa(provedor.nome)
            try:
                resposta = await provedor.responder(pergunta, modelo)
                self.metricas.registrar_sucesso(provedor.nome)
                break
            except ProvedorIndisponivel as erro:
                motivos[provedor.nome] = erro.motivo
                self.metricas.registrar_falha(provedor.nome, erro.motivo)
                proximo = ordem[posicao + 1].nome if posicao + 1 < len(ordem) else None
                if proximo:
                    aviso = ("provedor '%s' indisponível (%s); caindo para '%s'"
                             % (provedor.nome, erro.motivo, proximo))
                    self.metricas.registrar_fallback(aviso)
                    # Esta linha é a evidência FALLBACK_ACIONADO do laboratório.
                    print("[FALLBACK] %s" % aviso, flush=True)
                else:
                    print("[FALHA] provedor '%s' indisponível (%s) e não há "
                          "próximo na fila" % (provedor.nome, erro.motivo),
                          flush=True)
            except Exception as erro:  # noqa: BLE001
                # Um provedor com defeito não pode derrubar o gateway inteiro:
                # anota, trata como indisponível e segue a fila.
                motivo = "erro inesperado: %s" % type(erro).__name__
                motivos[provedor.nome] = motivo
                self.metricas.registrar_falha(provedor.nome, motivo)
                print("[ERRO] provedor '%s': %r" % (provedor.nome, erro), flush=True)

        if resposta is None:
            self.metricas.registrar_erro()
            raise TodosOsProvedoresIndisponiveis(motivos)

        registro = {
            "conteudo": resposta.conteudo,
            "modelo": resposta.modelo,
            "provedor": resposta.provedor,
            "tokens_estimados": resposta.tokens_estimados,
        }
        self.cache.guardar(pergunta, registro)

        return ResultadoDoGateway(
            conteudo=resposta.conteudo,
            modelo=resposta.modelo,
            provedor=resposta.provedor,
            tokens_estimados=resposta.tokens_estimados,
            origem_do_cache=None,
            similaridade=0.0,
            houve_fallback=len(tentados) > 1,
            tentativas=tentados,
            duracao_ms=int((time.perf_counter() - comeco) * 1000),
        )
