#!/usr/bin/env python3
"""Placar do Dojo ArenaLog.

Cada missão soma XP. O processo sai com 0 quando as missões 1 a 7 passam e, se os
quatro programas estiverem no ar, o boss também passa. Com os containers parados
o boss fica pendente e não derruba o placar.

Uso:
    python3 verificar.py
    python3 verificar.py --missao 3
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.abspath(__file__))

MISSOES = (
    (1, "Pasta no lugar", 100, "Recruta"),
    (2, "Elenco", 150, "Analista"),
    (3, "Conta da faixa", 250, "Estrategista"),
    (4, "Ciclo de vida", 150, "Juiz"),
    (5, "Janela de 48 horas", 200, "Cronista"),
    (6, "Placar sem dado pessoal", 150, "Narrador"),
    (7, "Testes prontos", 200, "Maestro"),
    (8, "Boss fight", 150, "Campeão"),
)


def ler(relativo):
    caminho = os.path.join(RAIZ, relativo)
    if not os.path.exists(caminho):
        return ""
    with open(caminho, encoding="utf-8") as arquivo:
        return arquivo.read()


def rodar(comando, cwd):
    processo = subprocess.run(
        comando,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return processo.returncode, processo.stdout


def missao_1():
    compose = ler("docker-compose.yml")
    faltas = []
    for nome in ("postgres", "elenco", "motor-ranking", "partidas", "placar"):
        if nome not in compose:
            faltas.append(f"serviço {nome} ausente")
    for url in (
        "http://elenco:8081",
        "http://motor-ranking:8000",
        "http://partidas:8080",
    ):
        if url not in compose:
            faltas.append(f"falta {url}")
    if "localhost" in compose:
        faltas.append("compose cita localhost; entre containers use o nome do serviço")
    for arquivo in (
        "elenco/Dockerfile",
        "motor-ranking/Dockerfile",
        "partidas/Dockerfile",
        "placar/Dockerfile",
        "db/init.sql",
        "motor-ranking/rivalidade.json",
    ):
        if not ler(arquivo):
            faltas.append(f"falta {arquivo}")
    init = ler("db/init.sql").lower()
    if "create schema elenco" not in init or "create schema partidas" not in init:
        faltas.append("init.sql não separa os schemas elenco e partidas")
    if "grant" in init and "partidas to elenco" in init:
        faltas.append("há grant cruzado de partidas para elenco")
    if "grant" in init and "elenco to partidas" in init:
        faltas.append("há grant cruzado de elenco para partidas")
    if faltas:
        return False, "; ".join(faltas)
    return True, "quatro programas, o banco e as duas gavetas"


def missao_node(pasta, teste):
    codigo, saida = rodar(["node", "--test", teste], os.path.join(RAIZ, pasta))
    if codigo != 0:
        ruins = [linha.strip() for linha in saida.splitlines() if linha.strip().startswith("not ok")]
        return False, ruins[0] if ruins else "node --test falhou"
    return True, "testes passaram"


def missao_python(pasta, arquivo):
    codigo, saida = rodar(
        [sys.executable, "-m", "unittest", arquivo],
        os.path.join(RAIZ, pasta),
    )
    if codigo != 0:
        linhas = [linha for linha in saida.splitlines() if linha.startswith("FAIL") or linha.startswith("ERROR") or "Error" in linha]
        resumo = linhas[-1] if linhas else "unittest falhou"
        return False, resumo
    return True, "testes passaram"


def missao_8():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8081/health", timeout=2) as resposta:
            if resposta.status != 200:
                return None, "elenco não respondeu 200"
    except (urllib.error.URLError, TimeoutError):
        return None, "containers parados; suba o compose para enfrentar o boss"
    codigo, saida = rodar([sys.executable, "scripts/boss.py"], RAIZ)
    if codigo != 0:
        ultima = saida.strip().splitlines()[-1] if saida.strip() else "boss em pé"
        return False, ultima
    return True, "boss derrotado"


FUNCOES = {
    1: missao_1,
    2: lambda: missao_node("elenco", "test/validar.test.js"),
    3: lambda: missao_python("motor-ranking", "test_ranking.py"),
    4: lambda: missao_python("partidas", "test_ciclo.py"),
    5: lambda: missao_python("partidas", "test_serie.py"),
    6: lambda: missao_node("placar", "test/agregar.test.js"),
    7: lambda: missao_python("partidas", "test_dubles.py"),
    8: missao_8,
}


def faixa(xp):
    if xp >= 1350:
        return "Lenda da Arena"
    if xp >= 1200:
        return "Campeão"
    if xp >= 1000:
        return "Maestro"
    if xp >= 800:
        return "Juiz"
    if xp >= 650:
        return "Estrategista"
    if xp >= 250:
        return "Analista"
    if xp >= 100:
        return "Recruta"
    return "Sem faixa"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--missao", type=int, choices=range(1, 9))
    args = parser.parse_args()
    escolhidas = [item for item in MISSOES if args.missao in (None, item[0])]

    print("ARENALOG DOJO")
    print("missão  nome                         XP   medalha")
    xp = 0
    obrigatorias_ok = True
    for numero, nome, pontos, medalha in escolhidas:
        ok, detalhe = FUNCOES[numero]()
        if ok is None:
            marca = "PENDENTE"
        elif ok:
            marca = "OK"
            xp += pontos
        else:
            marca = "ABERTA"
            obrigatorias_ok = False
        print(f"{numero:<7} {nome:<28} {pontos:>4}  {marca:<8} {medalha}")
        print(f"         {detalhe}")

    print(f"TOTAL {xp} / 1350 XP")
    print(f"FAIXA {faixa(xp)}")
    return 0 if obrigatorias_ok else 1


if __name__ == "__main__":
    sys.exit(main())
