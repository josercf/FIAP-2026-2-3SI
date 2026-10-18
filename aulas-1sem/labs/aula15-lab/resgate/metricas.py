"""
Contadores do AI Gateway da LogiTech.

Um gateway sem métrica é um proxy caro. O que justifica pôr uma camada
própria entre os serviços e os provedores de IA é justamente conseguir
responder, a qualquer momento, três perguntas que ninguém consegue responder
quando cada serviço tem a sua integração:

    quanto do tráfego foi servido pelo cache e não custou nada
    quantas vezes o provedor preferido falhou e o fallback salvou a chamada
    quanto de cada provedor a plataforma está usando

Tudo aqui é em memória e some quando o container reinicia. É o suficiente
para o laboratório e para a rota `GET /v1/metricas`.

Na Aula 15 este arquivo ganha uma quarta pergunta, e ela é de segurança:

    quantas entradas o guardrail recusou, e por qual regra
    quantos dados sensíveis a plataforma deixou de vazar hoje

Sem esses dois números, ligar guardrail é ato de fé. Com eles, a decisão de
afrouxar ou apertar uma regra passa a ter evidência, e o time descobre no
painel, e não pelo cliente, que uma regra nova começou a recusar gente
legítima.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field


@dataclass
class ContadorDeProvedor:
    """O que se sabe sobre um provedor desde que o gateway subiu."""

    tentativas: int = 0
    sucessos: int = 0
    falhas: int = 0
    ultimo_erro: str | None = None
    ultimo_uso: str | None = None

    def como_dicionario(self) -> dict:
        return {
            "tentativas": self.tentativas,
            "sucessos": self.sucessos,
            "falhas": self.falhas,
            "ultimo_erro": self.ultimo_erro,
            "ultimo_uso": self.ultimo_uso,
        }


@dataclass
class Metricas:
    """Estado observável do gateway.

    Protegido por trava: o Uvicorn atende várias requisições ao mesmo tempo,
    e `contador += 1` não é atômico em Python quando há troca de contexto no
    meio de uma chamada assíncrona.
    """

    requisicoes: int = 0
    respostas_ok: int = 0
    respostas_com_erro: int = 0

    acertos_exatos: int = 0
    acertos_por_similaridade: int = 0
    erros_de_cache: int = 0

    fallback_acionado: int = 0
    ultimo_motivo_de_fallback: str | None = None

    recusadas_por_limite: int = 0

    # Contadores de guardrail (ADR-009, seção 6).
    recusas_entrada: int = 0
    mascaramentos_saida: int = 0
    recusas_por_regra: dict[str, int] = field(default_factory=dict)

    provedores: dict[str, ContadorDeProvedor] = field(default_factory=dict)
    _trava: threading.Lock = field(default_factory=threading.Lock, repr=False)

    # -- registro -----------------------------------------------------

    def registrar_requisicao(self) -> None:
        with self._trava:
            self.requisicoes += 1

    def registrar_acerto_de_cache(self, tipo: str) -> None:
        with self._trava:
            if tipo == "exato":
                self.acertos_exatos += 1
            else:
                self.acertos_por_similaridade += 1

    def registrar_erro_de_cache(self) -> None:
        with self._trava:
            self.erros_de_cache += 1

    def registrar_tentativa(self, provedor: str) -> None:
        with self._trava:
            self.provedores.setdefault(provedor, ContadorDeProvedor()).tentativas += 1

    def registrar_sucesso(self, provedor: str) -> None:
        with self._trava:
            contador = self.provedores.setdefault(provedor, ContadorDeProvedor())
            contador.sucessos += 1
            contador.ultimo_uso = _agora()
            self.respostas_ok += 1

    def registrar_falha(self, provedor: str, motivo: str) -> None:
        with self._trava:
            contador = self.provedores.setdefault(provedor, ContadorDeProvedor())
            contador.falhas += 1
            contador.ultimo_erro = motivo

    def registrar_fallback(self, motivo: str) -> None:
        with self._trava:
            self.fallback_acionado += 1
            self.ultimo_motivo_de_fallback = motivo

    def registrar_recusa_por_limite(self) -> None:
        with self._trava:
            self.recusadas_por_limite += 1
            self.respostas_com_erro += 1

    def registrar_erro(self) -> None:
        with self._trava:
            self.respostas_com_erro += 1

    def registrar_recusa_de_entrada(self, regra: str) -> None:
        with self._trava:
            self.recusas_entrada += 1
            self.recusas_por_regra[regra] = self.recusas_por_regra.get(regra, 0) + 1
            self.respostas_com_erro += 1

    def registrar_mascaramento(self, quantidade: int) -> None:
        if quantidade <= 0:
            return
        with self._trava:
            self.mascaramentos_saida += quantidade

    # -- leitura ------------------------------------------------------

    def instantaneo(self, entradas_em_cache: int, limite_por_minuto: int,
                    estrategia: str, guardrails_ativos: bool = True) -> dict:
        """A fotografia que a rota GET /v1/metricas devolve."""
        with self._trava:
            acertos = self.acertos_exatos + self.acertos_por_similaridade
            consultas = acertos + self.erros_de_cache
            taxa = round(acertos / consultas, 4) if consultas else 0.0
            return {
                "requisicoes": self.requisicoes,
                "respostas_ok": self.respostas_ok,
                "respostas_com_erro": self.respostas_com_erro,
                "estrategia": estrategia,
                "cache": {
                    "acertos": acertos,
                    "acertos_exatos": self.acertos_exatos,
                    "acertos_por_similaridade": self.acertos_por_similaridade,
                    "erros": self.erros_de_cache,
                    "taxa_de_acerto": taxa,
                    "entradas": entradas_em_cache,
                },
                "fallback": {
                    "acionado": self.fallback_acionado,
                    "ultimo_motivo": self.ultimo_motivo_de_fallback,
                },
                "limite_de_taxa": {
                    "limite_por_minuto": limite_por_minuto,
                    "recusadas": self.recusadas_por_limite,
                },
                "provedores": {
                    nome: contador.como_dicionario()
                    for nome, contador in self.provedores.items()
                },
                "guardrail": {
                    "ativos": guardrails_ativos,
                    "recusas_entrada": self.recusas_entrada,
                    "mascaramentos_saida": self.mascaramentos_saida,
                    "recusas_por_regra": dict(self.recusas_por_regra),
                },
            }


def _agora() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
