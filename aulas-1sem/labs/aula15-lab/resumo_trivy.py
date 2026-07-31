#!/usr/bin/env python3
"""Resumo legível dos relatórios JSON que o `varrer.sh` gravou.

O Trivy tem saída de tabela própria, e ela é boa. Este resumo existe por dois
motivos que a tabela não atende:

1. Ele separa **o que tem correção publicada** do que não tem. Essa é a linha
   que decide entre corrigir (TODO-5) e registrar exceção (TODO-6), e é a
   pergunta que a tabela do Trivy não responde de relance.
2. Ele mostra o `PkgPath`, ou seja, **de onde dentro da imagem** o pacote veio.
   É o campo que resolve o Passo 5 sozinho.

    python3 resumo_trivy.py
    python3 resumo_trivy.py --detalhe logitech-notificacoes:aula15
"""

import argparse
import glob
import json
import os
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
PASTA = os.path.join(RAIZ, "relatorios")

# As imagens que o projeto constrói. É nelas, e só nelas, que vale o critério
# de zero CRITICAL da ADR-009.
DO_PROJETO = ("logitech-ai-gateway", "logitech-rag", "logitech-notificacoes")


def carregar():
    relatorios = []
    for caminho in sorted(glob.glob(os.path.join(PASTA, "*.json"))):
        try:
            with open(caminho, encoding="utf-8") as f:
                relatorios.append((caminho, json.load(f)))
        except (json.JSONDecodeError, OSError) as erro:
            print("  aviso: %s ilegível (%s)" % (os.path.basename(caminho), erro))
    return relatorios


def achados(dados):
    for resultado in dados.get("Results") or []:
        for v in resultado.get("Vulnerabilities") or []:
            yield resultado, v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--detalhe", help="imprime cada CVE da imagem indicada")
    args = ap.parse_args()

    relatorios = carregar()
    if not relatorios:
        print("Nenhum relatório em relatorios/. Rode ./varrer.sh primeiro.")
        return 1

    print("%-32s %9s %6s %6s %s" % ("IMAGEM", "CRITICAL", "HIGH", "S/COR", "ORIGEM"))
    print("-" * 78)
    criticas_do_projeto = 0

    for _, dados in relatorios:
        nome = dados.get("ArtifactName", "?")
        criticas = altas = sem_correcao = 0
        for _, v in achados(dados):
            if v["Severity"] == "CRITICAL":
                criticas += 1
            elif v["Severity"] == "HIGH":
                altas += 1
            if not v.get("FixedVersion"):
                sem_correcao += 1
        do_projeto = any(nome.startswith(p) for p in DO_PROJETO)
        if do_projeto:
            criticas_do_projeto += criticas
        print("%-32s %9d %6d %6d %s"
              % (nome[:32], criticas, altas, sem_correcao,
                 "projeto" if do_projeto else "terceiro"))

        if args.detalhe and args.detalhe in nome:
            for resultado, v in achados(dados):
                print("    %-16s %-9s %-22s %-12s -> %s"
                      % (v["VulnerabilityID"], v["Severity"], v["PkgName"],
                         v.get("InstalledVersion", "?"),
                         v.get("FixedVersion") or "SEM CORRECAO PUBLICADA"))
                if v.get("PkgPath"):
                    print("        de: %s" % v["PkgPath"])

    print("-" * 78)
    print("CRITICAL nas imagens do projeto: %d  (o critério da ADR-009 é zero)"
          % criticas_do_projeto)
    print("S/COR = achados sem versão corrigida publicada. São esses, e só")
    print("        esses, que viram exceção escrita em docs/EXCECOES.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
