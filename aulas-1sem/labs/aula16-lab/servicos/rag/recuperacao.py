"""
A recuperação do RAG, reduzida ao essencial para a Aula 15.

Não é tarefa. Não editem este arquivo.

Por que aqui a busca é lexical, e não vetorial
----------------------------------------------
A Aula 12 construiu a recuperação de verdade: `pgvector`, coluna
`vector(768)`, índice HNSW e distância de cosseno. **Aquela** é a
implementação da plataforma, e continua valendo.

Aqui a busca é por sobreposição de palavras sobre os mesmos contratos, em
memória, sem banco e sem modelo de embedding. A troca é deliberada e tem um
motivo só: **o assunto de hoje não é como o trecho foi encontrado, é o que
acontece com ele depois de encontrado.** Injeção indireta funciona igual se o
trecho veio de busca vetorial, de `ILIKE`, de um PDF anexado pelo cliente ou
de uma página que um agente abriu na internet. O ponto de entrada é o mesmo:
texto de terceiro entrando na janela de contexto com o mesmo status do texto
que você escreveu.

Trazer o pgvector para cá custaria dez minutos de subida de banco e de
reingestão, tirados do único bloco prático da noite, para provar algo que a
Aula 12 já provou.

O acervo é o mesmo `contratos/` da Aula 12, com **um arquivo a mais**.
"""

from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

PASTA_PADRAO = Path(os.environ.get("LOGITECH_CONTRATOS", "/app/contratos"))

_PONTUACAO = re.compile(r"[^\w\s]", re.UNICODE)
_ESPACOS = re.compile(r"\s+")

_VAZIAS = frozenset("""
a as ao aos o os um uma uns umas de do da dos das em no na nos nas por para
com sem sobre e ou que qual quais quando onde como meu minha meus minhas
esta este isso aquilo se ser sao foi entre ate apos pelo pela nao mais
""".split())


@dataclass
class Trecho:
    """Um pedaço de contrato, com a fonte que permite citá-lo."""

    arquivo: str
    cliente: str
    clausula: str
    texto: str
    nota: float = 0.0

    def como_dicionario(self) -> dict:
        return {
            "arquivo": self.arquivo,
            "cliente": self.cliente,
            "clausula": self.clausula,
            "texto": self.texto,
            "nota": round(self.nota, 4),
        }


def normalizar(texto: str) -> str:
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return _ESPACOS.sub(" ", _PONTUACAO.sub(" ", sem_acento.lower())).strip()


def _palavras(texto: str) -> frozenset[str]:
    return frozenset(p for p in normalizar(texto).split()
                     if len(p) > 2 and p not in _VAZIAS)


def carregar(pasta: Path | None = None) -> list[Trecho]:
    """Lê os contratos e quebra cada um por cláusula (`## Cláusula N`)."""
    pasta = pasta or PASTA_PADRAO
    trechos: list[Trecho] = []
    for arquivo in sorted(Path(pasta).glob("*.md")):
        bruto = arquivo.read_text(encoding="utf-8")
        cliente = arquivo.stem
        # O cabeçalho YAML não é conteúdo de cláusula, mas o nome do cliente
        # que está nele é o que permite a pergunta dizer "o contrato da Vale
        # Verde" sem que a cláusula repita o nome do cliente em cada parágrafo.
        if bruto.startswith("---"):
            partes = bruto.split("---", 2)
            achado = re.search(r"^cliente:\s*(.+)$", partes[1], re.MULTILINE)
            if achado:
                cliente = achado.group(1).strip()
            bruto = partes[2] if len(partes) > 2 else bruto
        blocos = re.split(r"\n(?=## )", bruto)
        for bloco in blocos:
            bloco = bloco.strip()
            if not bloco.startswith("## "):
                continue
            titulo = bloco.splitlines()[0].lstrip("# ").strip()
            trechos.append(Trecho(arquivo=arquivo.name, cliente=cliente,
                                  clausula=titulo, texto=bloco))
    return trechos


def recuperar(pergunta: str, acervo: list[Trecho], k: int = 3) -> list[Trecho]:
    """Devolve os `k` trechos que mais cobrem as palavras da pergunta.

    A nota é **cobertura** da pergunta, e não índice de Jaccard: quantas das
    palavras significativas da pergunta o trecho contém. Jaccard divide pela
    união e portanto pune trecho longo, o que aqui inverteria o resultado, já
    que cláusula de contrato varia de três linhas a trinta.
    """
    alvo = _palavras(pergunta)
    if not alvo:
        return []
    pontuados: list[Trecho] = []
    for trecho in acervo:
        palavras = _palavras(trecho.cliente + " " + trecho.clausula + " " + trecho.texto)
        if not palavras:
            continue
        nota = len(alvo & palavras) / len(alvo)
        if nota > 0:
            pontuados.append(Trecho(trecho.arquivo, trecho.cliente,
                                    trecho.clausula, trecho.texto, nota))
    # Empate resolvido pelo trecho mais curto: entre duas cláusulas que cobrem
    # a pergunta igual, a mais enxuta é a que responde.
    pontuados.sort(key=lambda t: (-t.nota, len(t.texto)))
    return pontuados[:k]
