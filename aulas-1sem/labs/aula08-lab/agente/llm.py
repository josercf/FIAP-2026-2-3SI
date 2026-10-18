#!/usr/bin/env python3
"""Os dois clientes de modelo do agente: o real e o simulado.

PRONTO: não é tarefa. Você usa, não escreve.

`ClienteOllama` fala com o Ollama local do devcontainer, o único backend de IA
dos laboratórios da disciplina (ADR-005). `ClienteSimulado` devolve respostas
de modelo **já formadas**, escritas à mão neste arquivo.

Por que o simulado existe, dito na cara e não escondido: o modelo local é
pequeno, e tool calling é justamente a tarefa em que modelo pequeno erra mais.
Se numa noite o `qwen3.5:2b` resolver responder em texto corrido em vez de
chamar a ferramenta, o laboratório inteiro pararia por um motivo que não tem
nada a ver com o que a aula ensina. Com o `--simular`, o Command Pattern, a
trilha de auditoria e as worktrees continuam exercitáveis do mesmo jeito.

O que o `--simular` NÃO faz: ele não simula os seus comandos. As chamadas ao
serviço de Pedidos são reais, a validação por JSON Schema é real e a auditoria
é real. O que vem pronto é apenas a intenção que, no outro modo, sairia do
modelo.
"""
import json
import os
import re
import urllib.error
import urllib.request

BASE_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
MODELO = os.environ.get("OLLAMA_MODEL", "qwen3.5:2b")
TIMEOUT = int(os.environ.get("AI_TIMEOUT", "300"))

INSTRUCAO_DE_SISTEMA = (
    "Você é o atendente virtual da LogiTech Enterprise, uma transportadora. "
    "Responda sempre em português do Brasil, de forma curta e objetiva. "
    "Você tem duas ferramentas e só age através delas: nunca invente status, "
    "prazo ou endereço. "
    "Para alterar um endereço de entrega você precisa do endereço completo, "
    "incluindo o CEP. Se o cliente não informou o CEP, peça o CEP a ele em vez "
    "de chamar a ferramenta com o campo faltando."
)


class ErroDoModelo(Exception):
    """Falha ao falar com o backend de modelo."""


# ---------------------------------------------------------------------------
# Cliente real: Ollama local
# ---------------------------------------------------------------------------
class ClienteOllama:
    """Cliente de tool calling do Ollama, só com a biblioteca padrão."""

    def __init__(self, modelo=None, base_url=None, timeout=TIMEOUT):
        self.modelo = modelo or MODELO
        self.base_url = (base_url or BASE_URL).rstrip("/")
        self.timeout = timeout

    @property
    def descricao(self):
        return "Ollama local, modelo %s" % self.modelo

    def no_ar(self):
        try:
            with urllib.request.urlopen(self.base_url + "/api/tags", timeout=5):
                return True
        except (urllib.error.URLError, OSError):
            return False

    def conversar(self, mensagens, ferramentas):
        """Manda a conversa e as ferramentas, devolve a mensagem do modelo.

        A mensagem devolvida é um dicionário no formato do Ollama, com
        `content` e, quando o modelo decide agir, `tool_calls`.
        """
        corpo = {
            "model": self.modelo,
            "messages": mensagens,
            "tools": ferramentas,
            "stream": False,
            # Temperatura baixa: em tool calling não se quer criatividade, se
            # quer o mesmo argumento sempre que a pergunta for a mesma.
            "options": {"temperature": 0.1},
        }
        req = urllib.request.Request(
            self.base_url + "/api/chat",
            data=json.dumps(corpo, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resposta:
                dados = json.loads(resposta.read().decode("utf-8"))
        except urllib.error.HTTPError as erro:
            detalhe = erro.read().decode("utf-8", "replace")[:300]
            raise ErroDoModelo(
                "o Ollama respondeu HTTP %d: %s\nSe o modelo não existe "
                "localmente, baixe com: ollama pull %s"
                % (erro.code, detalhe, self.modelo))
        except (urllib.error.URLError, OSError) as erro:
            raise ErroDoModelo(
                "não foi possível falar com o Ollama em %s (%s). Suba o "
                "servidor com 'ollama serve' ou rode o agente com --simular."
                % (self.base_url, erro))
        return dados.get("message") or {}


# ---------------------------------------------------------------------------
# Cliente simulado: respostas de modelo escritas à mão
# ---------------------------------------------------------------------------
def _chamada(nome, argumentos):
    return {"role": "assistant", "content": "",
            "tool_calls": [{"function": {"name": nome, "arguments": argumentos}}]}


def _fala(texto):
    return {"role": "assistant", "content": texto}


# Cada roteiro é a sequência de mensagens que o modelo produziria, uma por
# rodada do laço de conversa. Os identificadores e endereços são os do case
# LogiTech e existem de verdade no serviço de Pedidos congelado.
ROTEIROS = {
    "status": [
        _chamada("consultar_status_pedido", {"pedido_id": "PED-1042"}),
        _fala("O pedido PED-1042 está em trânsito com a Frota 07 e a última "
              "posição registrada é Ribeirão Preto, SP."),
    ],
    "endereco": [
        _chamada("alterar_endereco_entrega", {
            "pedido_id": "PED-1044",
            "logradouro": "Avenida Paulista",
            "numero": "1106",
            "complemento": "9o andar",
            "cidade": "São Paulo",
            "uf": "SP",
            "cep": "01311-000",
        }),
        _fala("Endereço de entrega do pedido PED-1044 atualizado para "
              "Avenida Paulista, 1106, São Paulo/SP, CEP 01311-000."),
    ],
    # O roteiro que interessa à lacuna TODO-5: a primeira intenção do modelo
    # vem SEM o CEP, é recusada pela validação, e só a segunda, já com o CEP,
    # chega a executar. Repare que quem corrige o modelo é a recusa auditada,
    # não uma instrução no prompt.
    "recusa": [
        _chamada("alterar_endereco_entrega", {
            "pedido_id": "PED-1043",
            "logradouro": "Rua Bela Cintra",
            "numero": "495",
            "cidade": "São Paulo",
            "uf": "SP",
        }),
        _chamada("alterar_endereco_entrega", {
            "pedido_id": "PED-1043",
            "logradouro": "Rua Bela Cintra",
            "numero": "495",
            "cidade": "São Paulo",
            "uf": "SP",
            "cep": "01415-000",
        }),
        _fala("Faltava o CEP na primeira tentativa, e por isso ela foi "
              "recusada antes de chegar ao sistema. Com o CEP 01415-000 "
              "informado, o endereço do pedido PED-1043 foi atualizado."),
    ],
    # Ferramenta inventada: acontece de verdade com modelo pequeno, e o
    # Despachante já trata. Serve para o aluno ver a recusa do Caso 1.
    "inventada": [
        _chamada("cancelar_pedido", {"pedido_id": "PED-1042"}),
        _fala("Não tenho ferramenta para cancelar pedidos. Posso consultar o "
              "status ou alterar o endereço de entrega."),
    ],
}


def escolher_roteiro(pergunta):
    """Escolhe o roteiro simulado a partir da pergunta do atendente.

    Regra simples e declarada: pedido de alteração de endereço com CEP no
    texto vira o roteiro autorizado; sem CEP, vira o roteiro da recusa.
    """
    texto = (pergunta or "").lower()
    if "cancel" in texto:
        return "inventada"
    if "endere" in texto or "mudar" in texto or "alterar" in texto:
        if re.search(r"\d{5}-?\d{3}", texto) or "cep" in texto:
            return "endereco"
        return "recusa"
    return "status"


class ClienteSimulado:
    """Devolve respostas de modelo já formadas, sem chamar modelo nenhum."""

    def __init__(self, roteiro=None):
        self.roteiro_forcado = roteiro
        self.passo = 0
        self.roteiro = None

    @property
    def descricao(self):
        return "modo --simular, roteiro %s" % (self.roteiro or self.roteiro_forcado
                                                or "escolhido pela pergunta")

    def no_ar(self):
        return True

    def conversar(self, mensagens, ferramentas):
        if self.roteiro is None:
            pergunta = ""
            for m in mensagens:
                if m.get("role") == "user":
                    pergunta = m.get("content", "")
                    break
            self.roteiro = self.roteiro_forcado or escolher_roteiro(pergunta)
        passos = ROTEIROS.get(self.roteiro)
        if passos is None:
            raise ErroDoModelo(
                "roteiro simulado '%s' não existe; disponíveis: %s"
                % (self.roteiro, ", ".join(sorted(ROTEIROS))))
        if self.passo >= len(passos):
            return _fala("Posso ajudar em mais alguma coisa?")
        mensagem = passos[self.passo]
        self.passo += 1
        # Cópia profunda barata: o laço de conversa acrescenta a mensagem ao
        # histórico, e um roteiro compartilhado não pode ser mutado por isso.
        return json.loads(json.dumps(mensagem, ensure_ascii=False))
