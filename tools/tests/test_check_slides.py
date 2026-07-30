#!/usr/bin/env python3
"""
Teste de regressao do tools/check_slides.py.

Roda o validador contra tools/tests/fixture_layout.html, que tem tres slides
com defeito conhecido, e confere que ele acusa o que deve e cala sobre o que
esta certo.

Existe por um motivo concreto: a checagem de sobreposicao foi escrita depois
que um aviso posicionado em absoluto cobriu o takeaway do slide 3 da Aula 02
sem que o validador dissesse nada. Sem este teste, nao ha garantia de que a
checagem continua funcionando.

Uso:
    python3 tools/tests/test_check_slides.py
"""
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VALIDADOR = os.path.join(RAIZ, "tools", "check_slides.py")
FIXTURE = os.path.join(RAIZ, "tools", "tests", "fixture_layout.html")

falhas = []


def checar(condicao, descricao, detalhe=""):
    print("[%s] %s" % ("PASSOU" if condicao else "FALHOU", descricao))
    if not condicao:
        falhas.append(descricao)
        if detalhe:
            print("         %s" % detalhe)


processo = subprocess.run(
    [sys.executable, VALIDADOR, os.path.relpath(FIXTURE, RAIZ)],
    cwd=RAIZ, capture_output=True, text=True,
)
saida = processo.stdout

print("=== saida do validador ===")
print("\n".join(l for l in saida.splitlines() if not l.startswith("127.0.0.1")))
print("=== assercoes ===")

blocos = saida.split("slide ")

checar(processo.returncode != 0,
       "o validador sai com codigo diferente de zero quando ha defeito",
       "codigo de saida foi %d" % processo.returncode)

checar("SOBREPOSICAO" in saida,
       "acusa a sobreposicao do slide 1",
       "nenhuma linha SOBREPOSICAO na saida: a checagem de sobreposicao parou de funcionar")

checar("ESTOURO" in saida,
       "acusa o estouro do slide 2",
       "nenhuma linha ESTOURO na saida")

# O slide 0 e limpo: nao pode aparecer no relatorio.
citou_slide_limpo = any(b.lstrip().startswith("0 ") for b in blocos[1:])
checar(not citou_slide_limpo,
       "nao acusa nada no slide 0, que esta limpo",
       "o slide limpo foi reportado: ha falso positivo")

# A sobreposicao do slide 1 nao pode ser confundida com estouro.
bloco_sobreposto = next((b for b in blocos[1:] if b.lstrip().startswith("1 ")), "")
checar("SOBREPOSICAO" in bloco_sobreposto,
       "a sobreposicao e reportada no slide certo",
       "o slide 1 nao trouxe SOBREPOSICAO")

print()
if falhas:
    print("%d assercao(oes) falharam." % len(falhas))
    sys.exit(1)
print("check_slides.py detecta estouro e sobreposicao, sem falso positivo.")
