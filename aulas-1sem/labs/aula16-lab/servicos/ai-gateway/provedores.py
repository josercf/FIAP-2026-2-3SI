"""
Os provedores de IA por trás da fachada.

Cada provedor é uma **estratégia intercambiável**: mesma interface, mesmo
tipo de entrada, mesmo tipo de saída, implementações completamente
diferentes por dentro. Quem chama o gateway nunca importa nada daqui.

Dois provedores, conforme a ADR-006:

    remoto   endpoint compatível com OpenAI, endereço e credencial vindos de
             variável de ambiente. **Indisponível na sala de aula**, porque
             não há chave para a turma. Se o professor preencher
             LOGITECH_IA_REMOTA_CHAVE, este caminho passa a responder sem que
             uma linha de código mude.

    local    o Ollama do devcontainer, backend único de IA da disciplina
             desde a ADR-005.

O fallback entre os dois é **real**, não encenado: a chamada ao remoto falha
de verdade por ausência de credencial, o gateway registra o motivo e passa ao
local. É a diferença entre ensinar resiliência e ensinar teatro.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import httpx


class ProvedorIndisponivel(RuntimeError):
    """Este provedor não pode atender agora. O gateway deve tentar o próximo."""

    def __init__(self, provedor: str, motivo: str) -> None:
        super().__init__("%s indisponível: %s" % (provedor, motivo))
        self.provedor = provedor
        self.motivo = motivo


@dataclass
class RespostaDeIA:
    """O que qualquer provedor devolve, independentemente de como o obteve."""

    conteudo: str
    modelo: str
    provedor: str
    tokens_estimados: int


@runtime_checkable
class ProvedorDeIA(Protocol):
    """A interface que a fachada conhece. Nada além disto.

    `por_que_indisponivel` existe para o diagnóstico: é uma checagem barata,
    sem tocar a rede, que responde "por que este provedor não deveria nem ser
    tentado agora". A rota `/health` usa isso para explicar o estado do
    gateway sem disparar chamada nenhuma a modelo.
    """

    nome: str

    def por_que_indisponivel(self) -> str | None: ...

    async def responder(self, pergunta: str, modelo: str | None = None) -> RespostaDeIA: ...


def _estimar_tokens(texto: str) -> int:
    """Aproximação grosseira e declarada: cerca de 4 caracteres por token.

    Não substitui o tokenizador do modelo. Serve para o painel de custo dar
    ordem de grandeza, que é o que a operação precisa no dia a dia.
    """
    return max(1, len(texto) // 4)


class ProvedorRemoto:
    """Endpoint compatível com o formato de chat da OpenAI.

    Não há chave para a turma, e é isso que torna o exercício honesto: este
    provedor falha primeiro, sempre, e o aluno vê o fallback acontecer no log
    e na rota de métricas.
    """

    nome = "remoto"

    def __init__(self) -> None:
        self.url = os.environ.get(
            "LOGITECH_IA_REMOTA_URL", "https://api.openai.com/v1/chat/completions")
        self.chave = os.environ.get("LOGITECH_IA_REMOTA_CHAVE", "").strip()
        self.modelo_padrao = os.environ.get("LOGITECH_IA_REMOTA_MODELO", "gpt-4o-mini")
        self.tempo_limite = float(os.environ.get("LOGITECH_IA_TIMEOUT_S", "20"))

    def por_que_indisponivel(self) -> str | None:
        if not self.chave:
            return ("credencial ausente: a variável LOGITECH_IA_REMOTA_CHAVE "
                    "está vazia, e a plataforma não envia requisição sem "
                    "credencial")
        return None

    async def responder(self, pergunta: str, modelo: str | None = None) -> RespostaDeIA:
        motivo = self.por_que_indisponivel()
        if motivo:
            # Falha antes de abrir socket: não se manda requisição sabidamente
            # inválida para um provedor pago só para "tentar".
            raise ProvedorIndisponivel(self.nome, motivo)

        escolhido = modelo or self.modelo_padrao
        try:
            async with httpx.AsyncClient(timeout=self.tempo_limite) as cliente:
                resposta = await cliente.post(
                    self.url,
                    headers={"Authorization": "Bearer %s" % self.chave},
                    json={
                        "model": escolhido,
                        "messages": [{"role": "user", "content": pergunta}],
                        "temperature": 0.2,
                    },
                )
        except httpx.HTTPError as erro:
            raise ProvedorIndisponivel(
                self.nome, "falha de rede: %s" % type(erro).__name__) from erro

        if resposta.status_code != 200:
            raise ProvedorIndisponivel(
                self.nome, "o provedor respondeu HTTP %d" % resposta.status_code)

        corpo = resposta.json()
        conteudo = corpo["choices"][0]["message"]["content"]
        return RespostaDeIA(
            conteudo=conteudo,
            modelo=corpo.get("model", escolhido),
            provedor=self.nome,
            tokens_estimados=corpo.get("usage", {}).get(
                "total_tokens", _estimar_tokens(pergunta + conteudo)),
        )


class ProvedorLocal:
    """O Ollama do devcontainer, backend único da disciplina (ADR-005).

    Dentro do Compose o Ollama não é um serviço da plataforma: ele roda no
    host, e o container alcança o host por `host.docker.internal`. É por isso
    que o serviço `ai-gateway` precisa de `extra_hosts` no docker-compose.yml
    quando o Docker roda em Linux, como no Codespace.
    """

    nome = "local"

    def __init__(self) -> None:
        self.url = os.environ.get(
            "LOGITECH_IA_OLLAMA_URL", "http://host.docker.internal:11434")
        self.modelo_padrao = os.environ.get("LOGITECH_IA_MODELO_LOCAL", "qwen2.5:1.5b")
        # 180 segundos, e não 20 como no remoto, por medição: a **primeira**
        # chamada a um modelo local ainda frio inclui carregar os pesos na
        # memória. Na validação deste laboratório, um "oi" ao qwen3.5:2b levou
        # 46 segundos na primeira vez e menos de 3 nas seguintes. Um timeout
        # curto transformaria essa lentidão de partida em "o Ollama está fora",
        # que é um diagnóstico errado.
        self.tempo_limite = float(os.environ.get("LOGITECH_IA_TIMEOUT_LOCAL_S", "180"))

    def por_que_indisponivel(self) -> str | None:
        # Nada barato a checar: só a chamada de verdade diz se o Ollama está
        # de pé. Devolver None aqui é a resposta honesta.
        return None

    async def responder(self, pergunta: str, modelo: str | None = None) -> RespostaDeIA:
        escolhido = modelo or self.modelo_padrao
        try:
            async with httpx.AsyncClient(timeout=self.tempo_limite) as cliente:
                resposta = await cliente.post(
                    "%s/api/chat" % self.url.rstrip("/"),
                    json={
                        "model": escolhido,
                        "messages": [{"role": "user", "content": pergunta}],
                        "stream": False,
                    },
                )
        except httpx.HTTPError as erro:
            raise ProvedorIndisponivel(
                self.nome,
                "o Ollama não respondeu em %s (%s). Ele está de pé? "
                "O roteiro do laboratório manda pará-lo antes do compose up."
                % (self.url, type(erro).__name__)) from erro

        if resposta.status_code != 200:
            raise ProvedorIndisponivel(
                self.nome, "o Ollama respondeu HTTP %d" % resposta.status_code)

        corpo = resposta.json()
        conteudo = corpo.get("message", {}).get("content", "").strip()
        if not conteudo:
            raise ProvedorIndisponivel(self.nome, "o modelo devolveu resposta vazia")

        return RespostaDeIA(
            conteudo=conteudo,
            modelo=corpo.get("model", escolhido),
            provedor=self.nome,
            tokens_estimados=corpo.get("eval_count")
            or _estimar_tokens(pergunta + conteudo),
        )


def montar_provedores() -> list[ProvedorDeIA]:
    """Instancia os provedores configurados. Ordem aqui é irrelevante: quem
    decide a ordem de tentativa é a estratégia de roteamento."""
    return [ProvedorRemoto(), ProvedorLocal()]
