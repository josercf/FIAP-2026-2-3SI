"""Guardrails do AI Gateway da LogiTech: entrada e saída.

Contrato da ADR-009, seção 6:

    Entrada  detecta tentativa de sobrescrever a instrução de sistema e
             recusa, devolvendo 422 com {"recusado": true, "motivo": "..."}
    Saída    mascara dado sensível antes de devolver:
                 CPF     -> ***.***.***-**
                 cartão  -> **** **** **** 1234
                 placa   -> AAA*****
    Métricas guardrail.recusas_entrada e guardrail.mascaramentos_saida
    Chave    LOGITECH_GUARDRAILS_ATIVOS, padrão true a partir da Aula 15

Por que a detecção de entrada não é uma lista de palavras proibidas
-------------------------------------------------------------------
Porque lista de palavra proibida não é defesa: quem escreve o ataque escolhe
as palavras. O que está aqui procura **o padrão de sobrescrita**, que é a
combinação de um verbo de anulação com um alvo que é a própria instrução do
sistema, ou a tentativa de abrir um turno de papel que só o servidor pode
abrir.

Ainda assim, isto é uma heurística e falha. O laboratório da Aula 15 obriga
o aluno a tentar quebrar o próprio filtro e a registrar uma formulação que
passou, em `FORMULACAO_QUE_PASSOU`. Filtro que ninguém tentou furar não é
defesa, é decoração. Em produção esta camada seria acompanhada de um
classificador e de limitação do que a ferramenta consegue fazer.

Não é tarefa na Aula 16. Este arquivo vem pronto, e o que a Aula 16 exige é
que ele esteja **ligado** e que a recusa esteja registrada.
"""

from __future__ import annotations

import os
import re
import unicodedata

# --------------------------------------------------------------------------
# Entrada: sobrescrita de instrução
# --------------------------------------------------------------------------

_ANULACAO = (
    r"(?:ignor\w*|desconsider\w*|esquec\w*|desprez\w*|anul\w*|revog\w*|"
    r"sobrescrev\w*|substitu\w*|disregard|ignore|forget|override)"
)
_ALVO = (
    r"(?:as?\s+)?(?:tod\w+\s+)?(?:sua[s]?\s+|the\s+)?"
    r"(?:instru\w*|orienta\w*|regra\w*|diretriz\w*|prompt|system\s*prompt|"
    r"mensagem\s+de\s+sistema|instructions?|rules?)"
)

PADROES_DE_INJECAO = [
    (
        "sobrescrita_de_instrucao",
        re.compile(r"%s[^.\n]{0,40}%s" % (_ANULACAO, _ALVO), re.IGNORECASE),
        "a mensagem pede para ignorar ou substituir as instrucoes do sistema",
    ),
    (
        "turno_de_sistema_forjado",
        re.compile(r"(?:^|\n)\s*(?:system|sistema|assistant|assistente)\s*[:>]", re.IGNORECASE),
        "a mensagem tenta abrir um turno de sistema, que so o servidor abre",
    ),
    (
        "marcador_de_conversa_forjado",
        re.compile(r"(?:<\|[^|>]{1,24}\|>|\[/?(?:INST|SYS)\]|###\s*(?:system|instruction))",
                   re.IGNORECASE),
        "a mensagem carrega marcador de formato de conversa do modelo",
    ),
    (
        "exfiltracao_de_instrucao",
        re.compile(r"(?:revel\w*|mostr\w*|imprim\w*|repita|repeat|print|reveal|show)"
                   r"[^.\n]{0,40}(?:system\s*prompt|prompt\s+de\s+sistema|"
                   r"suas?\s+instru\w*|your\s+instructions?)", re.IGNORECASE),
        "a mensagem tenta extrair a instrucao de sistema",
    ),
    (
        "elevacao_de_papel",
        re.compile(r"(?:voce|voce\s+agora|a\s+partir\s+de\s+agora|you\s+are\s+now|"
                   r"from\s+now\s+on)[^.\n]{0,30}"
                   r"(?:sem\s+restri\w*|sem\s+filtro|modo\s+desenvolvedor|"
                   r"developer\s+mode|dan|jailbreak|no\s+restrictions?)", re.IGNORECASE),
        "a mensagem tenta trocar o papel do modelo por um sem restricao",
    ),
]


class EntradaRecusada(Exception):
    """A entrada bateu num padrão de injeção. Vira 422, não 400 nem 500."""

    def __init__(self, regra: str, motivo: str):
        super().__init__(motivo)
        self.regra = regra
        self.motivo = motivo


def ativos() -> bool:
    """Padrão `true` a partir da Aula 15 (ADR-009).

    O laboratório manda **desligar** para ver a injeção dar certo e ligar
    para ver a defesa funcionar. O aluno precisa ver o ataque acontecer, ou
    a defesa vira ritual.
    """
    return os.environ.get("LOGITECH_GUARDRAILS_ATIVOS", "true").strip().lower() not in (
        "0", "false", "nao", "não", "off",
    )


def _sem_acento(texto: str) -> str:
    """Normaliza para o padrão não ser furado por acento ou por letra grega.

    `ignore` e `ignoré` precisam bater na mesma regra, e a decomposição
    Unicode resolve isso sem multiplicar expressão regular.
    """
    return "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )


def inspecionar_entrada(pergunta: str) -> None:
    """Levanta `EntradaRecusada` quando a pergunta tenta sobrescrever o sistema."""
    if not ativos():
        return
    normalizada = _sem_acento(pergunta)
    for regra, padrao, motivo in PADROES_DE_INJECAO:
        if padrao.search(normalizada):
            raise EntradaRecusada(regra, motivo)


# --------------------------------------------------------------------------
# Saída: mascaramento de dado sensível
# --------------------------------------------------------------------------

_CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
_CARTAO = re.compile(r"\b(?:\d[ .-]?){12}(\d{4})\b")
_PLACA = re.compile(r"\b([A-Z]{3})-?\d[A-Z0-9]\d{2}\b")


def mascarar_saida(texto: str) -> tuple:
    """Devolve `(texto_mascarado, quantidade_de_mascaramentos)`.

    O formato de cada máscara é o da ADR-009 e não é livre: o verificador da
    Aula 16 confere a string exata. Máscara com formato próprio por serviço
    seria mais um lugar em que duas stacks discordam.
    """
    if not ativos():
        return texto, 0

    contagem = 0

    def trocar_cpf(_):
        nonlocal contagem
        contagem += 1
        return "***.***.***-**"

    def trocar_cartao(m):
        nonlocal contagem
        contagem += 1
        return "**** **** **** %s" % m.group(1)

    def trocar_placa(m):
        nonlocal contagem
        contagem += 1
        return "%s*****" % m.group(1)

    # O cartão vem antes do CPF de propósito: onze dígitos de um CPF cabem
    # dentro de dezesseis de um cartão, e mascarar o CPF primeiro deixaria
    # metade do número do cartão exposta.
    texto = _CARTAO.sub(trocar_cartao, texto)
    texto = _CPF.sub(trocar_cpf, texto)
    texto = _PLACA.sub(trocar_placa, texto)
    return texto, contagem
