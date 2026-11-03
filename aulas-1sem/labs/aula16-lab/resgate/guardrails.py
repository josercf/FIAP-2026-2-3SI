"""
GABARITO do `servicos/ai-gateway/guardrails.py` (TODO-1 e TODO-2).

Copie por cima do arquivo do serviço só se travar, e registre
`USEI_O_RESGATE` em `docs/EVIDENCIAS.md`.

    cp resgate/guardrails.py servicos/ai-gateway/guardrails.py

Leia os comentários: eles dizem por que cada regra existe e, principalmente,
o que cada uma **não** pega.
"""

from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Interruptor (ADR-009, seção 6). Padrão `true` a partir da Aula 15.
# ---------------------------------------------------------------------------

VERDADEIROS = frozenset({"1", "true", "sim", "on", "yes"})


def ativos() -> bool:
    """Lê `LOGITECH_GUARDRAILS_ATIVOS`. Padrão `true`.

    O interruptor existe para o laboratório poder mostrar o ataque
    funcionando antes de mostrar a defesa. Ele é declarado, aparece no
    README e no slide: não é porta dos fundos escondida.
    """
    return os.environ.get("LOGITECH_GUARDRAILS_ATIVOS", "true").strip().lower() in VERDADEIROS


# ---------------------------------------------------------------------------
# Normalização: a mesma ideia do cache lexical da Aula 07
# ---------------------------------------------------------------------------

_ESPACOS = re.compile(r"\s+")


def normalizar(texto: str) -> str:
    """Tira acento, caixa e colapsa espaço, sem tirar pontuação.

    A pontuação fica porque `###`, `[` e `---` são parte de alguns dos
    ataques: quem escreve uma falsa instrução de sistema costuma imitar
    marcadores de formatação.
    """
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return _ESPACOS.sub(" ", sem_acento.lower()).strip()


# ---------------------------------------------------------------------------
# TODO-1: detector de sobrescrita de instrução
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Veredito:
    """O que o guardrail de entrada concluiu sobre um texto."""

    recusado: bool
    motivo: str = ""
    regra: str = ""


# Quatro famílias de tentativa, e cada uma tem um jeito diferente de falhar.
#
#   revogacao    manda esquecer o que veio antes
#   troca-papel  redefine quem o assistente é
#   exfiltracao  pede o próprio prompt de volta
#   falso-sistema imita marcador de instrução de sistema dentro do texto
#
# A quarta é a que pega a injeção **indireta**: um documento envenenado quase
# nunca diz "ignore as instruções", ele finge ser uma seção de sistema.
REGRAS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "revogacao",
        re.compile(
            r"\b(ignor\w*|esquec\w*|desconsider\w*|apagu?\w*|revogu?\w*|anul\w*)\b"
            r"[^.\n]{0,40}?\b(instruc\w*|regras|orientac\w*|diretriz\w*|ordens|comandos)\b"
        ),
        "a mensagem pede para revogar as instruções que o assistente já tem",
    ),
    (
        "revogacao",
        re.compile(
            r"\b(instruc\w*|regras|orientac\w*)\b[^.\n]{0,40}?"
            r"\b(anteriores|acima|previas|originais)\b[^.\n]{0,40}?"
            r"\b(revogad\w*|canceladas|invalidas|sem efeito|nao valem)\b"
        ),
        "a mensagem declara que as instruções anteriores foram revogadas",
    ),
    (
        "troca-papel",
        re.compile(
            r"\b(voce (nao e mais|agora e|passa a ser)"
            r"|a partir de agora,? voce"
            r"|assuma o papel|adote o papel|finja ser|aja como se fosse"
            r"|modo (desenvolvedor|depuracao|debug|manutencao|irrestrito))\b"
        ),
        "a mensagem tenta redefinir quem o assistente é",
    ),
    (
        "exfiltracao",
        re.compile(
            r"\b(repit\w*|imprim\w*|mostr\w*|revel\w*|exib\w*|list\w*|transcrev\w*|"
            r"reproduz\w*|copi\w*)\b[^.\n]{0,60}?"
            r"\b(prompt|instruc\w*|regras internas|orientac\w*|contexto|"
            r"mensagem de sistema)\b"
        ),
        "a mensagem pede que o assistente devolva as próprias instruções",
    ),
    (
        "exfiltracao",
        re.compile(r"\b(prompt de sistema|system prompt|regra interna|regras internas)\b"),
        "a mensagem cita explicitamente o prompt de sistema",
    ),
    (
        "falso-sistema",
        re.compile(
            r"(\[\s*nota de sistema|nota de sistema para|instruc\w* de sistema|"
            r"###\s*(sistema|system)|<\s*system\s*>|"
            r"\bprioridade maxima\b|\bfim do (contexto|documento)\b|"
            r"\bnova instruc\w* de sistema\b)"
        ),
        "a mensagem imita um marcador de instrução de sistema dentro do texto",
    ),
    (
        "revogacao",
        re.compile(
            r"\b(ignore|disregard|forget|override)\b[^.\n]{0,40}?"
            r"\b(previous|prior|above|all)\b|\byou are now\b|\bsystem prompt\b"
        ),
        "a mesma tentativa, escrita em inglês",
    ),
]


def inspecionar_entrada(texto: str) -> Veredito:
    """Decide se uma entrada tenta sobrescrever a instrução de sistema.

    Devolve `Veredito(recusado=True, ...)` na primeira regra que casa. A
    primeira que casa é a que aparece no 422, e é por isso que o campo
    `regra` existe: recusar sem dizer qual regra disparou torna o filtro
    impossível de depurar e de auditar.
    """
    alvo = normalizar(texto)
    for nome, padrao, motivo in REGRAS:
        if padrao.search(alvo):
            return Veredito(recusado=True, motivo=motivo, regra=nome)
    return Veredito(recusado=False)


# ---------------------------------------------------------------------------
# TODO-2: mascaramento de dado sensível na saída
# ---------------------------------------------------------------------------
#
# O formato é **fixo pela ADR-009, seção 6**. Não invente outro: a Aula 16
# testa a plataforma inteira contra estes três formatos.
#
#     CPF     ***.***.***-**
#     cartão  **** **** **** 1234      (os quatro últimos dígitos ficam)
#     placa   AAA*****
#
# O cartão mantém os quatro últimos porque é assim que o atendente confirma
# com o cliente qual cartão é, sem que o número inteiro apareça em log, em
# print de tela ou no histórico da conversa. É a mesma razão de a fatura do
# seu cartão vir assim.

MASCARA_CPF = "***.***.***-**"
MASCARA_PLACA = "AAA*****"

# A ordem destas expressões importa e é a parte não óbvia do exercício.
# Um cartão "4111 1111 1111 1234" contém, no meio, uma sequência que a
# expressão do CPF também aceita. Mascarar CPF primeiro estraga o cartão e
# faz o contador mentir. Cartão primeiro, CPF depois, placa por último.
CARTAO = re.compile(r"\b(?:\d{4}[ .\-]?){3}(\d{4})\b")
CPF = re.compile(r"\b\d{3}[.\s]?\d{3}[.\s]?\d{3}[-\s]?\d{2}\b")
# Placa Mercosul (RJX2A19) e placa antiga (RJX-2019 ou RJX2019).
PLACA = re.compile(r"\b[A-Z]{3}[ \-]?\d[A-Z0-9]\d{2}\b")


def mascarar_saida(texto: str) -> tuple[str, int]:
    """Devolve `(texto_mascarado, quantidade_de_substituicoes)`.

    A quantidade alimenta o contador `guardrail.mascaramentos_saida`. Contar
    substituição, e não resposta afetada, é o que permite ao painel dizer
    "vazariam 214 documentos esta semana" em vez de "houve 30 respostas com
    algum problema".
    """
    total = 0

    texto, n = CARTAO.subn(lambda m: "**** **** **** %s" % m.group(1), texto)
    total += n

    texto, n = CPF.subn(MASCARA_CPF, texto)
    total += n

    texto, n = PLACA.subn(MASCARA_PLACA, texto)
    total += n

    return texto, total
