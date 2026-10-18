"""
Políticas de borda do gateway: cache de respostas e limite de taxa.

As duas existem pelo mesmo motivo: chamada de LLM é cara e lenta. A primeira
evita pagar duas vezes pela mesma pergunta; a segunda evita que um serviço
com defeito consuma a cota da plataforma inteira em dez segundos.

Sobre "caching semântico", com honestidade
------------------------------------------
Caching semântico de verdade transforma a pergunta em um **vetor de
embeddings** e procura, no banco vetorial, a pergunta mais próxima por
similaridade de cosseno. "Onde está meu pedido?" e "cadê minha encomenda?"
viram vetores vizinhos e compartilham a mesma resposta, mesmo sem uma palavra
em comum.

Aqui a similaridade é **lexical**, calculada por índice de Jaccard sobre as
palavras normalizadas. É uma aproximação: pega variação de pontuação, de
caixa, de acento e de ordem das palavras, e não pega sinônimo. Fizemos assim
de propósito, para que o laboratório rode sem depender de um modelo de
embeddings e de um banco vetorial que a plataforma ainda não tem. O
mecanismo (normalizar, medir distância, aceitar acima de um limiar) é o
mesmo; o que muda é como a distância é medida. O banco vetorial chega no
Módulo III.
"""

from __future__ import annotations

import hashlib
import os
import re
import threading
import time
import unicodedata
from collections import deque
from dataclasses import dataclass

_PONTUACAO = re.compile(r"[^\w\s]", re.UNICODE)
_ESPACOS = re.compile(r"\s+")

# Palavras muito frequentes atrapalham a medida de similaridade: duas
# perguntas completamente diferentes compartilhariam "de", "o", "que".
_VAZIAS = frozenset("""
a as ao aos o os um uma uns umas de do da dos das em no na nos nas por para
com sem sobre e ou que qual quais quando onde como meu minha meus minhas
esta este isso aquilo eh e_ ja se ser esta estao foi sao
""".split())


def normalizar(texto: str) -> str:
    """Reduz a pergunta à sua forma comparável.

    Tira acento, caixa e pontuação, e colapsa espaço. "Onde está o PEDIDO
    4471?" e "onde esta o pedido 4471" viram a mesma coisa.
    """
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    sem_pontuacao = _PONTUACAO.sub(" ", sem_acento.lower())
    return _ESPACOS.sub(" ", sem_pontuacao).strip()


def _palavras_significativas(texto_normalizado: str) -> frozenset[str]:
    return frozenset(
        p for p in texto_normalizado.split() if p and p not in _VAZIAS
    )


def similaridade(a: frozenset[str], b: frozenset[str]) -> float:
    """Índice de Jaccard: interseção sobre união. Zero a um."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


@dataclass
class EntradaDeCache:
    pergunta_normalizada: str
    palavras: frozenset[str]
    resposta: dict
    gravada_em: float


class CacheDeRespostas:
    """Cache de duas camadas: acerto exato e acerto por similaridade.

    O acerto exato é uma busca por hash, imediata. Só quando ele falha vale
    a pena percorrer as entradas comparando similaridade, e o custo disso é
    limitado pelo teto de entradas.
    """

    def __init__(self, limiar: float | None = None, ttl_s: int | None = None,
                 maximo: int | None = None) -> None:
        self.limiar = float(
            limiar if limiar is not None
            else os.environ.get("LOGITECH_IA_LIMIAR_SIMILARIDADE", "0.72"))
        self.ttl_s = int(
            ttl_s if ttl_s is not None
            else os.environ.get("LOGITECH_IA_CACHE_TTL_S", "600"))
        self.maximo = int(
            maximo if maximo is not None
            else os.environ.get("LOGITECH_IA_CACHE_MAXIMO", "200"))
        self._por_hash: dict[str, EntradaDeCache] = {}
        self._ordem: deque[str] = deque()
        self._trava = threading.Lock()

    def __len__(self) -> int:
        return len(self._por_hash)

    @staticmethod
    def _chave(texto_normalizado: str) -> str:
        return hashlib.sha256(texto_normalizado.encode("utf-8")).hexdigest()

    def _expirada(self, entrada: EntradaDeCache, agora: float) -> bool:
        return agora - entrada.gravada_em > self.ttl_s

    def consultar(self, pergunta: str) -> tuple[dict | None, str | None, float]:
        """Devolve (resposta, tipo_do_acerto, similaridade).

        `tipo_do_acerto` é "exato", "similaridade" ou None.
        """
        texto = normalizar(pergunta)
        chave = self._chave(texto)
        agora = time.time()

        with self._trava:
            entrada = self._por_hash.get(chave)
            if entrada and not self._expirada(entrada, agora):
                return entrada.resposta, "exato", 1.0

            palavras = _palavras_significativas(texto)
            melhor: EntradaDeCache | None = None
            melhor_nota = 0.0
            for candidata in self._por_hash.values():
                if self._expirada(candidata, agora):
                    continue
                nota = similaridade(palavras, candidata.palavras)
                if nota > melhor_nota:
                    melhor, melhor_nota = candidata, nota

            if melhor is not None and melhor_nota >= self.limiar:
                return melhor.resposta, "similaridade", round(melhor_nota, 4)

        return None, None, 0.0

    def guardar(self, pergunta: str, resposta: dict) -> None:
        texto = normalizar(pergunta)
        chave = self._chave(texto)
        with self._trava:
            if chave not in self._por_hash:
                self._ordem.append(chave)
            self._por_hash[chave] = EntradaDeCache(
                pergunta_normalizada=texto,
                palavras=_palavras_significativas(texto),
                resposta=resposta,
                gravada_em=time.time(),
            )
            # Descarte pela ordem de chegada quando o teto é atingido.
            while len(self._ordem) > self.maximo:
                antiga = self._ordem.popleft()
                self._por_hash.pop(antiga, None)

    def limpar(self) -> None:
        with self._trava:
            self._por_hash.clear()
            self._ordem.clear()


class LimiteExcedido(RuntimeError):
    """O cliente estourou a cota da janela atual."""

    def __init__(self, limite: int, segundos_para_liberar: int) -> None:
        super().__init__(
            "limite de %d requisições por minuto excedido" % limite)
        self.limite = limite
        self.segundos_para_liberar = segundos_para_liberar


class LimitadorDeTaxa:
    """Janela deslizante de 60 segundos, por cliente.

    O gateway é um ponto único: sem limite, um laço com defeito em um serviço
    consome a cota que os outros sete precisariam. O limite é por chave de
    cliente (aqui, o cabeçalho `X-Servico`), não global, para que o serviço
    que errou não derrube os demais.
    """

    JANELA_S = 60

    def __init__(self, limite_por_minuto: int | None = None) -> None:
        self.limite = int(
            limite_por_minuto if limite_por_minuto is not None
            else os.environ.get("LOGITECH_IA_LIMITE_POR_MINUTO", "30"))
        self._janelas: dict[str, deque[float]] = {}
        self._trava = threading.Lock()

    def permitir(self, cliente: str) -> None:
        """Levanta LimiteExcedido quando o cliente estourou a cota."""
        if self.limite <= 0:
            return
        agora = time.time()
        with self._trava:
            janela = self._janelas.setdefault(cliente, deque())
            while janela and agora - janela[0] > self.JANELA_S:
                janela.popleft()
            if len(janela) >= self.limite:
                espera = int(self.JANELA_S - (agora - janela[0])) + 1
                raise LimiteExcedido(self.limite, espera)
            janela.append(agora)
