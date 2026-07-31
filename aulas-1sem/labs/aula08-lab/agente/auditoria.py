#!/usr/bin/env python3
"""Trilha de auditoria do agente, gravada em `docs/AUDITORIA.md`.

PRONTO: não é tarefa. Os seus Commands e o Despachante chamam `registrar`.

Cada linha da trilha responde a uma pergunta que o compliance da LogiTech vai
fazer depois de qualquer incidente: **quem pediu o quê, quando, com quais
argumentos, e o que o sistema decidiu**. É a metade do Command Pattern que a
integração ingênua nunca tem: quando o modelo chama a API direto, não sobra
registro nenhum além do log do servidor, que não sabe que houve uma IA no meio.

O arquivo é Markdown para ser legível no GitHub, mas o formato de linha é
estável de propósito: `verificar.py` conta autorizações e recusas a partir
dele.
"""
import json
import os
from datetime import datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMINHO_PADRAO = os.path.join(RAIZ, "docs", "AUDITORIA.md")

AUTORIZADO = "AUTORIZADO"
RECUSADO = "RECUSADO"
FALHOU = "FALHOU"

CABECALHO = """# Trilha de auditoria do agente da LogiTech

Cada linha é uma decisão tomada pelo Despachante do agente. Este arquivo é
escrito pelo código, não à mão: `agente/auditoria.py` acrescenta uma linha por
evento. `verificar.py` conta as linhas `AUTORIZADO` e `RECUSADO` daqui.

| Momento | Ferramenta | Veredito | Argumentos | Resultado |
|---|---|---|---|---|
"""


def _resumir(valor, limite=160):
    """Serializa argumentos ou resultado em uma linha de tabela Markdown.

    Escapa o caractere de barra vertical, senão um endereço com `|` no meio
    quebraria a tabela e, pior, quebraria a contagem do verificador.
    """
    if isinstance(valor, (dict, list)):
        texto = json.dumps(valor, ensure_ascii=False, sort_keys=True)
    else:
        texto = str(valor)
    texto = texto.replace("|", "/").replace("\n", " ").strip()
    if len(texto) > limite:
        texto = texto[: limite - 3] + "..."
    return texto or "-"


def registrar(ferramenta, veredito, argumentos, resultado, caminho=None):
    """Acrescenta um evento à trilha de auditoria.

    - `ferramenta`: nome declarado da ferramenta, por exemplo
      `alterar_endereco_entrega`.
    - `veredito`: `AUTORIZADO`, `RECUSADO` ou `FALHOU`.
    - `argumentos`: o que o modelo pediu, exatamente como pediu.
    - `resultado`: o que aconteceu, ou o motivo da recusa.
    - `caminho`: destino alternativo, usado pelos testes e pelo `verificar.py`
      para não sujar a trilha real do aluno.

    Devolve o caminho do arquivo escrito.
    """
    destino = caminho or CAMINHO_PADRAO
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    novo = not os.path.exists(destino) or os.path.getsize(destino) == 0

    linha = "| %s | %s | %s | %s | %s |\n" % (
        datetime.now().replace(microsecond=0).isoformat(),
        ferramenta,
        veredito,
        _resumir(argumentos),
        _resumir(resultado),
    )
    with open(destino, "a", encoding="utf-8") as f:
        if novo:
            f.write(CABECALHO)
        f.write(linha)
    return destino


def contar(caminho=None):
    """Conta os vereditos registrados na trilha.

    Devolve um dicionário com as chaves `AUTORIZADO`, `RECUSADO` e `FALHOU`.
    """
    destino = caminho or CAMINHO_PADRAO
    contagem = {AUTORIZADO: 0, RECUSADO: 0, FALHOU: 0}
    if not os.path.exists(destino):
        return contagem
    with open(destino, encoding="utf-8") as f:
        for linha in f:
            if not linha.startswith("|"):
                continue
            colunas = [c.strip() for c in linha.strip().strip("|").split("|")]
            if len(colunas) < 3:
                continue
            if colunas[2] in contagem:
                contagem[colunas[2]] += 1
    return contagem
