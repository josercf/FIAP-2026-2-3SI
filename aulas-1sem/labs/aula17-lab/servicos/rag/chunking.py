"""Chunking: como um contrato de 8 páginas vira dezenas de trechos.

Esta é a primeira etapa do pipeline RAG, e a que mais decide a qualidade da
recuperação. Um trecho grande dilui o significado e o vetor fica "sobre tudo e
sobre nada". Um trecho pequeno perde o contexto e recupera meia frase.

A estratégia aqui é **chunking por cláusula com teto de tamanho**, e não corte
cego a cada N caracteres. Contrato tem estrutura, e jogar essa estrutura fora
para cortar de 700 em 700 caracteres é perder informação de graça.

Não é tarefa. Este arquivo vem pronto, e os dois parâmetros do topo são o que
vale a pena experimentar depois da aula.
"""

import re

# Teto de caracteres por trecho. Cláusula maior que isso é quebrada em
# parágrafos, mantendo o título da cláusula em cada pedaço.
TAMANHO_MAXIMO = 1200

# Piso: trecho menor que isso é grudado no seguinte. Evita que um título solto
# vire uma linha na tabela e ocupe uma posição no ranking sem dizer nada.
TAMANHO_MINIMO = 180


def ler_cabecalho(bruto: str) -> tuple[dict, str]:
    """Separa o cabeçalho YAML do corpo Markdown.

    Devolve (metadados, corpo). Os metadados viram as colunas `cliente`,
    `titulo` e `vigencia` da tabela `conhecimento.contratos`, que é a razão de
    a tabela existir: sem ela, esses três campos estariam repetidos em cada uma
    das dezenas de linhas de `trechos`.
    """
    metadados: dict[str, str] = {}
    corpo = bruto

    if bruto.startswith("---"):
        partes = bruto.split("---", 2)
        if len(partes) == 3:
            for linha in partes[1].strip().splitlines():
                if ":" in linha:
                    chave, valor = linha.split(":", 1)
                    metadados[chave.strip()] = valor.strip()
            corpo = partes[2]

    return metadados, corpo.strip()


def dividir(corpo: str) -> list[str]:
    """Divide o corpo do contrato em trechos, na ordem em que aparecem."""
    # Cada cláusula começa em um cabeçalho de nível 2. O lookahead mantém o
    # cabeçalho no início do bloco em vez de descartá-lo no separador.
    blocos = re.split(r"\n(?=##\s)", corpo)

    trechos: list[str] = []
    for bloco in blocos:
        bloco = bloco.strip()
        if not bloco:
            continue
        if len(bloco) <= TAMANHO_MAXIMO:
            trechos.append(bloco)
            continue

        # Cláusula longa: quebra por parágrafo, repetindo o título em cada
        # pedaço. Sem essa repetição, o segundo pedaço da Cláusula 7 vira um
        # texto sobre prazos que não diz de que assunto está falando, e a busca
        # semântica passa longe dele.
        linhas = bloco.splitlines()
        titulo = linhas[0] if linhas[0].startswith("##") else ""
        restante = "\n".join(linhas[1:]).strip()

        atual = ""
        for paragrafo in re.split(r"\n\s*\n", restante):
            paragrafo = paragrafo.strip()
            if not paragrafo:
                continue
            candidato = (atual + "\n\n" + paragrafo).strip()
            if len(candidato) > TAMANHO_MAXIMO and atual:
                trechos.append((titulo + "\n\n" + atual).strip())
                atual = paragrafo
            else:
                atual = candidato
        if atual:
            trechos.append((titulo + "\n\n" + atual).strip())

    return _juntar_curtos(trechos)


def _juntar_curtos(trechos: list[str]) -> list[str]:
    """Cola trechos abaixo do piso no vizinho seguinte."""
    saida: list[str] = []
    pendente = ""
    for trecho in trechos:
        candidato = (pendente + "\n\n" + trecho).strip() if pendente else trecho
        if len(candidato) < TAMANHO_MINIMO:
            pendente = candidato
            continue
        saida.append(candidato)
        pendente = ""
    if pendente:
        if saida:
            saida[-1] = saida[-1] + "\n\n" + pendente
        else:
            saida.append(pendente)
    return saida
